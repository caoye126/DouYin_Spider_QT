import json
import os
import re
import time
import openpyxl
import requests
from loguru import logger
from retry import retry


def norm_str(str):
    new_str = re.sub(r"|[\\/:*?\"<>| ]+", "", str).replace('\n', '').replace('\r', '')
    return new_str

def norm_text(text):
    ILLEGAL_CHARACTERS_RE = re.compile(r'[\000-\010]|[\013-\014]|[\016-\037]')
    text = ILLEGAL_CHARACTERS_RE.sub(r'', text)
    return text


def timestamp_to_str(timestamp):
    try:
        ts = int(timestamp)
        if ts > 10000000000: # 可能是毫秒
            ts = ts / 1000
        time_local = time.localtime(ts)
        dt = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
        return dt
    except:
        return str(timestamp)



def handle_work_info(data):
    # 安全获取字段值
    def safe_get(obj, key, default='未知'):
        if isinstance(obj, dict) and key in obj:
            return obj[key]
        return default
    
    author = data.get('author', {})
    if not author:
        author = data.get('user', {}) # 兼容某些接口

    sec_uid = safe_get(author, 'sec_uid', '未知')
    user_url = f'https://www.douyin.com/user/{sec_uid}' if sec_uid != '未知' else '未知'
    user_desc = safe_get(author, 'signature', '未知')
    following_count = safe_get(author, 'following_count', '未知')
    follower_count = safe_get(author, 'follower_count', '未知')
    total_favorited = safe_get(author, 'total_favorited', '未知')
    aweme_count = safe_get(author, 'aweme_count', '未知')
    user_id = safe_get(author, 'unique_id', '未知')
    user_age = safe_get(author, 'user_age', '未知')
    gender = safe_get(author, 'gender', '未知')
    if gender == 1:
        gender = '男'
    elif gender == 0:
        gender = '女'
    else:
        gender = '未知'
    
    ip_location = data.get('ip_label', '未知')
    if ip_location == '未知':
        ip_location = data.get('user', {}).get('ip_location', '未知')
    
    aweme_id = safe_get(data, 'aweme_id', '未知')
    nickname = safe_get(author, 'nickname', '未知')
    
    # 安全获取头像URL
    try:
        avatar_list = author.get('avatar_thumb', {}).get('url_list', [])
        if avatar_list and len(avatar_list) > 0:
            author_avatar = avatar_list[0]
        else:
            author_avatar = '未知'
    except:
        author_avatar = '未知'
    
    # 安全获取视频封面URL
    try:
        cover_list = data.get('video', {}).get('cover', {}).get('url_list', [])
        if cover_list and len(cover_list) > 0:
            video_cover = cover_list[0]
        else:
            video_cover = '未知'
    except:
        video_cover = '未知'
    
    title = safe_get(data, 'desc', '未知')
    desc = safe_get(data, 'desc', '未知')
    
    stats = data.get('statistics', {})
    admire_count = safe_get(stats, 'admire_count', 0)
    digg_count = safe_get(stats, 'digg_count', 0)
    comment_count = safe_get(stats, 'comment_count', 0)
    collect_count = safe_get(stats, 'collect_count', 0)
    share_count = safe_get(stats, 'share_count', 0)
    
    # 安全获取视频地址
    try:
        url_list = data.get('video', {}).get('play_addr', {}).get('url_list', [])
        if url_list and len(url_list) > 0:
            video_addr = url_list[0]
        else:
            video_addr = '未知'
    except:
        video_addr = '未知'
    
    # 获取图片列表 (图集)
    image_urls = []
    images = data.get('images', [])
    if not images:
        images = data.get('image_post_info', {}).get('images', [])
    
    if isinstance(images, list):
        for img in images:
            if isinstance(img, dict):
                u_list = img.get('url_list', [])
                if u_list:
                    image_urls.append(u_list[0])
            elif isinstance(img, str):
                image_urls.append(img)

    create_time = safe_get(data, 'create_time', '未知')

    text_extra = data.get('text_extra', [])
    topics = []
    if isinstance(text_extra, list):
        for item in text_extra:
            if isinstance(item, dict):
                hashtag_name = item.get('hashtag_name', '')
                if hashtag_name:
                    topics.append(hashtag_name)

    work_type = '视频'
    aweme_type = data.get('aweme_type', -1)
    if aweme_type in [68, 150]:
        work_type = '图集'
    elif aweme_type in [0, 2, 4]:
        work_type = '视频'
    elif image_urls: # 如果有图片列表，也认为是图集
        work_type = '图集'

    return {
        'work_id': aweme_id,
        'work_url': f'https://www.douyin.com/video/{aweme_id}',
        'work_type': work_type,
        'title': title,
        'desc': desc,
        'admire_count': admire_count,
        'digg_count': digg_count,
        'comment_count': comment_count,
        'collect_count': collect_count,
        'share_count': share_count,
        'video_addr': video_addr,
        'images': image_urls,  # 返回列表
        'topics': topics,      # 返回列表
        'create_time': create_time,
        'video_cover': video_cover,
        'user_url': user_url,
        'user_id': user_id,
        'nickname': nickname,
        'author_avatar': author_avatar,
        'user_desc': user_desc,
        'following_count': following_count,
        'follower_count': follower_count,
        'total_favorited': total_favorited,
        'aweme_count': aweme_count,
        'user_age': user_age,
        'gender': gender,
        'ip_location': ip_location
    }


def save_to_xlsx(datas, file_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    headers = ['作品id', '作品url', '作品类型', '作品标题', '描述', 'admire数量', '点赞数量', '评论数量', '收藏数量', '分享数量', '视频地址url', '图片地址url列表', '标签', '上传时间', '视频封面url', '用户主页url', '用户id', '昵称', '头像url', '用户描述', '关注数量', '粉丝数量', '作品被赞和收藏数量', '作品数量', '用户年龄', '性别', 'ip归属地']
    ws.append(headers)
    for data in datas:
        processed_row = []
        key_order = [
            'work_id', 'work_url', 'work_type', 'title', 'desc', 
            'admire_count', 'digg_count', 'comment_count', 'collect_count', 'share_count',
            'video_addr', 'images', 'topics', 'create_time', 'video_cover',
            'user_url', 'user_id', 'nickname', 'author_avatar', 'user_desc',
            'following_count', 'follower_count', 'total_favorited', 'aweme_count',
            'user_age', 'gender', 'ip_location'
        ]
        
        for k in key_order:
            v = data.get(k, '')
            if k == 'create_time' and v != '未知':
                val = timestamp_to_str(v)
            elif isinstance(v, list):
                val = '; '.join([str(i) for i in v])
            elif isinstance(v, dict):
                val = json.dumps(v, ensure_ascii=False)
            else:
                val = str(v)
            processed_row.append(norm_text(val))
        ws.append(processed_row)
        
    wb.save(file_path)
    logger.info(f'数据保存至 {file_path}')

def download_media(path, name, url, type, max_retries=2):
    """
    下载媒体文件（图片或视频）
    :param path: 保存路径
    :param name: 文件名
    :param url: 下载URL
    :param type: 文件类型（image或video）
    :param max_retries: 最大重试次数（包括首次尝试）
    :return: True表示成功，False表示失败
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://www.douyin.com/',
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }
    
    if type == 'image':
        for attempt in range(max_retries):
            try:
                res = requests.get(url, headers=headers, timeout=30)
                res.raise_for_status()
                with open(os.path.join(path, name + '.jpg'), mode="wb") as f:
                    f.write(res.content)
                logger.debug(f'图片下载成功: {name}.jpg')
                return True
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f'图片下载失败（第{attempt + 1}次尝试）: {name}.jpg, 错误: {e}，进行重试...')
                    time.sleep(1)  # 重试前等待1秒
                else:
                    logger.error(f'图片下载失败（已重试{max_retries}次）: {name}.jpg, 错误: {e}')
                    return False
    elif type == 'video':
        for attempt in range(max_retries):
            try:
                res = requests.get(url, headers=headers, stream=True, timeout=30)
                res.raise_for_status()
                size = 0
                chunk_size = 1024 * 1024
                with open(os.path.join(path, name + '.mp4'), mode="wb") as f:
                    for data in res.iter_content(chunk_size=chunk_size):
                        if data:
                            f.write(data)
                            size += len(data)
                logger.debug(f'视频下载成功: {name}.mp4, 大小: {size} bytes')
                return True
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f'视频下载失败（第{attempt + 1}次尝试）: {name}.mp4, 错误: {e}，进行重试...')
                    time.sleep(1)  # 重试前等待1秒
                else:
                    logger.error(f'视频下载失败（已重试{max_retries}次）: {name}.mp4, 错误: {e}')
                    with open(os.path.join(path, name + '.mp4'), mode="wb") as f:
                        f.write(b'')
                    return False
    
    return False


def save_wrok_detail(work, path):
    with open(os.path.join(path, 'detail.txt'), mode="w", encoding="utf-8") as f:
        f.write(f"作品id: {work['work_id']}\n")
        f.write(f"作品url: {work['work_url']}\n")
        f.write(f"作品类型: {work['work_type']}\n")
        f.write(f"作品标题: {work['title']}\n")
        f.write(f"描述: {work['desc']}\n")
        f.write(f"admire数量: {work['admire_count']}\n")
        f.write(f"点赞数量: {work['digg_count']}\n")
        f.write(f"评论数量: {work['comment_count']}\n")
        f.write(f"收藏数量: {work['collect_count']}\n")
        f.write(f"分享数量: {work['share_count']}\n")
        f.write(f"视频地址url: {work['video_addr']}\n")
        
        images = work.get('images', [])
        images_str = '; '.join(images) if isinstance(images, list) else str(images)
        f.write(f"图片地址url列表: {images_str}\n")
        
        topics = work.get('topics', [])
        topics_str = '; '.join(topics) if isinstance(topics, list) else str(topics)
        f.write(f"标签: {topics_str}\n")
        
        f.write(f"上传时间: {timestamp_to_str(work['create_time'])}\n")
        f.write(f"视频封面url: {work['video_cover']}\n")
        f.write(f"用户主页url: {work['user_url']}\n")
        f.write(f"用户id: {work['user_id']}\n")
        f.write(f"昵称: {work['nickname']}\n")
        f.write(f"头像url: {work['author_avatar']}\n")
        f.write(f"用户描述: {work['user_desc']}\n")
        f.write(f"关注数量: {work['following_count']}\n")
        f.write(f"粉丝数量: {work['follower_count']}\n")
        f.write(f"作品被赞和收藏数量: {work['total_favorited']}\n")
        f.write(f"作品数量: {work['aweme_count']}\n")
        f.write(f"用户年龄: {work['user_age']}\n")
        f.write(f"用户性别: {work['gender']}\n")
        f.write(f"ip归属地: {work['ip_location']}\n")


def check_work_already_downloaded(save_path, work_type):
    """
    检查作品是否已经下载过
    :param save_path: 保存路径
    :param work_type: 作品类型（图集或视频）
    :return: True表示已下载，False表示未下载
    """
    if not os.path.exists(save_path):
        return False
    
    # 检查是否存在视频文件和图片文件
    has_video = os.path.exists(os.path.join(save_path, 'video.mp4'))
    has_images = False
    
    # 检查是否存在图片文件（image_0.jpg, image_1.jpg 等）
    for file in os.listdir(save_path):
        if file.startswith('image_') and file.endswith('.jpg'):
            has_images = True
            break
    
    # 根据作品类型判断是否已下载
    if work_type == '视频':
        # 视频作品：检查是否存在 video.mp4
        return has_video
    elif work_type == '图集':
        # 图集作品：检查是否存在至少一张图片
        return has_images
    
    return False


@retry(tries=3, delay=1)
def download_work(work_info, path, save_choice):
    work_id = work_info['work_id']
    user_id = work_info['user_id']
    title = work_info['title']
    title = norm_str(title)[:40]
    nickname = work_info['nickname']
    nickname = norm_str(nickname)[:20]
    if not title or title.strip() == '':
        title = f'无标题'
    
    save_path = os.path.join(path, f'{nickname}_{user_id}', f'{title}_{work_id}')
    
    # 检查作品是否已经下载过
    work_type = work_info['work_type']
    if check_work_already_downloaded(save_path, work_type):
        logger.info(f'作品 {work_id} 已存在，跳过下载: {save_path}')
        return save_path
    
    check_and_create_path(save_path)
    
    with open(os.path.join(save_path, 'info.json'), mode='w', encoding='utf-8') as f:
        f.write(json.dumps(work_info, ensure_ascii=False) + '\n')
        
    work_type = work_info['work_type']
    save_wrok_detail(work_info, save_path)
    
    if work_type == '图集' and save_choice in ['media', 'media-image', 'all']:
        images = work_info.get('images', [])
        if isinstance(images, list):
            for img_index, img_url in enumerate(images):
                if img_url and img_url != '未知':
                    download_media(save_path, f'image_{img_index}', img_url, 'image')
    elif work_type == '视频' and save_choice in ['media', 'media-video', 'all']:
        video_cover = work_info.get('video_cover', '')
        video_addr = work_info.get('video_addr', '')
        # 跳过下载封面 cover.jpg
        # if video_cover and video_cover != '未知':
        #     download_media(save_path, 'cover', video_cover, 'image')
        if video_addr and video_addr != '未知':
            download_media(save_path, 'video', video_addr, 'video')
            
    logger.info(f'作品 {work_info["work_id"]} 处理完成，保存路径: {save_path}')
    return save_path



def check_and_create_path(path):
    if not os.path.exists(path):
        try:
            os.makedirs(path, exist_ok=True)
        except Exception as e:
            logger.error(f"创建路径失败: {path}, 错误: {e}")
            raise

