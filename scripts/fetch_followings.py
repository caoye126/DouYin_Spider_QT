#!/usr/bin/env python3
import os
import sys
import csv
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from builder.auth import DouyinAuth
from dy_apis.douyin_api import DouyinAPI
from utils.requester import SessionState, Requester, batch_runner
import logging

logging.basicConfig(level=logging.INFO)


def load_cookie_from_env_file(env_path):
    if not os.path.exists(env_path):
        return None
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                k, v = line.split('=', 1)
                if k.strip() == 'DOUYIN_COOKIE':
                    return v.strip().strip('"')
    return None


def extract_sec_uid(item):
    # try several common keys
    for key in ('sec_uid', 'secUserId', 'sec_user_id', 'secUserIdStr'):
        if key in item:
            return item.get(key)
    if 'user' in item and isinstance(item['user'], dict):
        for key in ('sec_uid', 'sec_user_id', 'secUserId', 'secUserIdStr'):
            if key in item['user']:
                return item['user'].get(key)
    return None


def extract_nickname(item):
    if 'nickname' in item:
        return item.get('nickname')
    if 'user' in item and isinstance(item['user'], dict):
        return item['user'].get('nickname')
    # fallback to possible nested keys
    for k in ('display_name', 'short_id'):
        if k in item:
            return item.get(k)
    return ''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cookie', help='DOUYIN_COOKIE string (overrides .env)')
    parser.add_argument('--sec_uid', help='manual sec_uid (overrides auto-detection)')
    parser.add_argument('--out', default='follow_list.csv', help='output CSV file')
    parser.add_argument('--num', type=int, default=5000, help='max number of followings to fetch')
    args = parser.parse_args()

    cookie_str = args.cookie
    if not cookie_str:
        env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
        cookie_str = load_cookie_from_env_file(env_path)
    if not cookie_str:
        cookie_str = os.environ.get('DOUYIN_COOKIE')
    if not cookie_str:
        print('ERROR: No DOUYIN_COOKIE found. Provide with --cookie, .env DOUYIN_COOKIE, or env var.')
        return

    auth = DouyinAuth()
    auth.perepare_auth(cookie_str)

    try:
        user_id = str(auth.get_uid())
    except Exception as e:
        print('获取 user_id 失败:', e)
        return

    # 优先使用手动传入的 sec_uid（如果提供）
    if args.sec_uid:
        sec_uid = args.sec_uid
    else:
        # 尝试获取 sec_uid，包含多个回退方式以防页面结构变化
        try:
            sec_uid = DouyinAPI.get_my_sec_uid(auth)
        except Exception:
            sec_uid = None
        if not sec_uid:
            # 回退：尝试直接请求首页查找 secUid / sec_uid / secUserId
            try:
                import requests
                from builder.header import HeaderBuilder, HeaderType
                headers = HeaderBuilder().build(HeaderType.DOC)
                headers.set_header('cookie', auth.cookie_str)
                resp = requests.get('https://www.douyin.com/', headers=headers.get(), cookies=auth.cookie, timeout=15, verify=False)
                import re
                # 检索多种可能的键名
                for pattern in [r'"secUid"\s*:\s*"(.*?)"', r'"sec_uid"\s*:\s*"(.*?)"', r'"secUserId"\s*:\s*"(.*?)"']:
                    m = re.findall(pattern, resp.text)
                    if m:
                        sec_uid = m[0]
                        break
            except Exception:
                sec_uid = None
    if not sec_uid:
        print('获取 sec_uid 失败：未能在响应中找到 secUid，可能是 Cookie 无效或页面结构已变。')
        print('解决方法：1) 提供有效的 DOUYIN_COOKIE；2) 手动传入 sec_uid（命令行参数 --sec_uid）')
        print('示例：')
        print('python scripts/fetch_followings.py --sec_uid MS4wLjABAAAA... --cookie "msToken=...; s_v_web_id=..."')
        return

    logging.info('获取到 user_id=%s sec_uid=%s，开始拉取关注列表...', user_id, sec_uid)

    # 配置：遵循你给定的策略
    per_session_qps = 0.3  # 0.2-0.5 r/s 推荐值
    batch_size = 30  # 20-50
    batch_pause_min = 30
    batch_pause_max = 120
    max_retries = 5
    initial_backoff = 5.0
    backoff_multiplier = 2.0
    jitter = 0.2
    failure_threshold = 10
    isolation_seconds = 60 * 30

    session_state = SessionState(session_id=sec_uid or user_id, qps=per_session_qps)
    requester = Requester(session_state,
                          max_retries=max_retries,
                          initial_backoff=initial_backoff,
                          backoff_multiplier=backoff_multiplier,
                          jitter=jitter,
                          failure_threshold=failure_threshold,
                          isolation_seconds=isolation_seconds)

    # worker_func: fetch followings for a batch (we'll ask API for num = sum of batch sizes)
    def worker(requester_obj, batch_items):
        # batch_items contains dummy placeholders; we will request by pages using DouyinAPI.get_some_user_following_list
        # since the API returns up to the requested num, for simplicity request len(batch_items) per batch
        num = len(batch_items)
        # wrap the DouyinAPI call via requester
        def call_api():
            return DouyinAPI.get_some_user_following_list(auth, user_id, sec_uid, num)

        res = requester_obj.call(call_api)
        # normalize results
        rows_local = []
        for it in res:
            nickname = extract_nickname(it)
            sec = extract_sec_uid(it)
            if not sec and 'user' in it and isinstance(it['user'], dict):
                sec = extract_sec_uid(it['user'])
            if not sec:
                sec = it.get('uid') or it.get('id')
            url = f'https://www.douyin.com/user/{sec}' if sec else ''
            rows_local.append({'nickname': nickname, 'sec_uid': sec, 'url': url})
        return rows_local

    # create dummy task list length = desired num, batch_runner groups accordingly
    tasks = list(range(args.num))
    results = batch_runner(tasks, worker, requester, batch_size=batch_size, batch_pause_min=batch_pause_min, batch_pause_max=batch_pause_max)

    out_path = os.path.join(os.path.dirname(__file__), '..', args.out)
    with open(out_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['nickname', 'sec_uid', 'url'])
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    logging.info('完成：已保存 %d 条到 %s', len(results), out_path)


if __name__ == '__main__':
    main()
