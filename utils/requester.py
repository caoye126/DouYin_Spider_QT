import time
import threading
import random
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)


class CircuitOpenError(Exception):
    pass


class SessionState:
    def __init__(self, session_id: str, qps: float = 0.3):
        self.session_id = session_id
        self.qps = qps
        self.min_interval = 1.0 / qps if qps > 0 else 0
        self._lock = threading.Lock()
        self._last_request_ts = 0.0
        self.failures = 0
        self.isolated_until = 0.0

    def wait_for_slot(self):
        with self._lock:
            now = time.time()
            elapsed = now - self._last_request_ts
            need = self.min_interval - elapsed
            if need > 0:
                jitter = random.uniform(0.8, 1.2)
                sleep_t = need * jitter
                logger.debug('Session %s sleeping %.2fs to respect rate', self.session_id, sleep_t)
                time.sleep(sleep_t)
            self._last_request_ts = time.time()

    def record_failure(self):
        self.failures += 1

    def record_success(self):
        self.failures = 0

    def isolate(self, seconds: int):
        self.isolated_until = time.time() + seconds
        logger.warning('Session %s isolated for %ds', self.session_id, seconds)

    def is_isolated(self) -> bool:
        return time.time() < self.isolated_until


class Requester:
    def __init__(self,
                 session_state: SessionState,
                 max_retries: int = 5,
                 initial_backoff: float = 5.0,
                 backoff_multiplier: float = 2.0,
                 jitter: float = 0.2,
                 failure_threshold: int = 10,
                 isolation_seconds: int = 1800):
        self.session = session_state
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.backoff_multiplier = backoff_multiplier
        self.jitter = jitter
        self.failure_threshold = failure_threshold
        self.isolation_seconds = isolation_seconds

    def call(self, func: Callable, *args, **kwargs) -> Any:
        if self.session.is_isolated():
            raise CircuitOpenError(f'session {self.session.session_id} is isolated until {self.session.isolated_until}')

        attempt = 0
        backoff = self.initial_backoff
        while attempt <= self.max_retries:
            if self.session.is_isolated():
                raise CircuitOpenError(f'session {self.session.session_id} is isolated')

            # rate control
            self.session.wait_for_slot()

            try:
                result = func(*args, **kwargs)

                # Detect certain failure-like responses: None, empty, or dict with status code
                if result is None:
                    raise Exception('empty response')

                # simple heuristic: if result is dict and contains error codes or HTTP-like status
                if isinstance(result, dict):
                    st = None
                    for key in ('status_code', 'status', 'code'):
                        if key in result:
                            try:
                                st = int(result.get(key))
                            except Exception:
                                st = None
                            break
                    if st in (403, 429):
                        raise Exception(f'HTTP {st}')

                # success
                self.session.record_success()
                return result

            except CircuitOpenError:
                raise
            except Exception as e:
                attempt += 1
                self.session.record_failure()
                logger.warning('Request attempt %d failed: %s', attempt, e)
                if self.session.failures >= self.failure_threshold:
                    # isolate session
                    iso = int(self.isolation_seconds * random.uniform(0.9, 1.1))
                    self.session.isolate(iso)
                    raise CircuitOpenError(f'session {self.session.session_id} isolated after {self.session.failures} failures')

                if attempt > self.max_retries:
                    logger.error('Exceeded max retries (%d)', self.max_retries)
                    raise

                # exponential backoff with jitter
                jitter_factor = random.uniform(1 - self.jitter, 1 + self.jitter)
                sleep_t = backoff * jitter_factor
                logger.info('Backoff sleeping %.2fs before retry', sleep_t)
                time.sleep(sleep_t)
                backoff *= self.backoff_multiplier


def batch_runner(task_items, worker_func: Callable, requester: Requester, batch_size: int = 30, batch_pause_min: int = 30, batch_pause_max: int = 120):
    """
    Run tasks in batches. worker_func(requester, items_batch) -> list of results
    """
    results = []
    total = len(task_items)
    i = 0
    while i < total:
        batch = task_items[i:i + batch_size]
        logger.info('Processing batch %d - %d (%d items)', i + 1, i + len(batch), len(batch))
        try:
            res = worker_func(requester, batch)
            if res:
                results.extend(res)
        except CircuitOpenError as e:
            logger.error('Circuit open: %s', e)
            # when circuit opens, sleep longer
            pause = int((batch_pause_min + batch_pause_max) / 2)
            logger.info('Sleeping %ds due to circuit open', pause)
            time.sleep(pause)
        except Exception as e:
            logger.exception('Batch processing failed: %s', e)

        i += batch_size
        if i < total:
            pause = random.randint(batch_pause_min, batch_pause_max)
            logger.info('Batch pause %ds before next batch', pause)
            time.sleep(pause)

    return results
