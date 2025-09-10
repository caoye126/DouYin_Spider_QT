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
    time_local = time.localtime(timestamp / 1000)
    dt = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
    return dt



def handle_work_info(data):
    # 安全获取字段值，处理字典和列表类型
    def safe_get(obj, key, default='未知'):
        if isinstance(obj, dict) and key in obj:
            value = obj[key]
            if isinstance(value, (dict, list)):
                return str(value)  # 将复杂类型转换为字符串
            return value
        return default
    
    sec_uid = safe_get(data['author'], 'sec_uid', '未知')
    user_url = f'https://www.douyin.com/user/{sec_uid}' if sec_uid != '未知' else '未知'
    user_desc = safe_get(data['author'], 'signature', '未知')
    following_count = safe_get(data['author'], 'following_count', '未知')
    follower_count = safe_get(data['author'], 'follower_count', '未知')
    total_favorited = safe_get(data['author'], 'total_favorited', '未知')
    aweme_count = safe_get(data['author'], 'aweme_count', '未知')
    user_id = safe_get(data['author'], 'unique_id', '未知')
    user_age = safe_get(data['author'], 'user_age', '未知')
    gender = safe_get(data['author'], 'gender', '未知')
    if gender == 1:
        gender = '男'
    elif gender == 0:
        gender = '女'
    else:
        gender = '未知'
    try:
        ip_location = safe_get(data, 'user', {}).get('ip_location', '未知')
    except:
        ip_location = '未知'
    aweme_id = safe_get(data, 'aweme_id', '未知')
    nickname = safe_get(data['author'], 'nickname', '未知')
    
    # 安全获取头像URL
    try:
        avatar_list = data.get('author', {}).get('avatar_thumb', {}).get('url_list', [])
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
    admire_count = safe_get(data['statistics'], 'admire_count', 0)
    digg_count = safe_get(data['statistics'], 'digg_count', 0)
    commnet_count = safe_get(data['statistics'], 'comment_count', 0)
    collect_count = safe_get(data['statistics'], 'collect_count', 0)
    share_count = safe_get(data['statistics'], 'share_count', 0)
    
    # 安全获取视频地址
    try:
        url_list = data.get('video', {}).get('play_addr', {}).get('url_list', [])
        if url_list and len(url_list) > 0:
            video_addr = url_list[0]
        else:
            video_addr = '未知'
    except:
        video_addr = '未知'
    
    images = safe_get(data, 'images', [])
    if not isinstance(images, list):
        images = []
    create_time = safe_get(data, 'create_time', '未知')

    text_extra = safe_get(data, 'text_extra', [])
    text_extra = text_extra if text_extra else []
    topics = []
    for item in text_extra:
        if isinstance(item, dict):
            hashtag_name = safe_get(item, 'hashtag_name', '')
            if hashtag_name:
                topics.append(hashtag_name)

    work_type = '未知'
    aweme_type = safe_get(data, 'aweme_type', -1)
    if aweme_type == 68:
        work_type = '图集'
    elif aweme_type == 0:
        work_type = '视频'

    return {
        'work_id': aweme_id,
        'work_url': f'https://www.douyin.com/video/{aweme_id}',
        'work_type': work_type,
        'title': title,
        'desc': desc,
        'admire_count': admire_count,
        'digg_count': digg_count,
        'comment_count': commnet_count,
        'collect_count': collect_count,
        'share_count': share_count,
        'video_addr': video_addr,
        'images': '; '.join(images) if images else '',  # 将列表转换为字符串
        'topics': '; '.join(topics) if topics else '',  # 将列表转换为字符串
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
        # 处理数据，确保所有值都是字符串
        processed_data = {}
        for k, v in data.items():
            if isinstance(v, dict):
                # 如果是字典，转换为JSON字符串
                import json
                processed_data[k] = norm_text(json.dumps(v, ensure_ascii=False))
            elif isinstance(v, list):
                # 如果是列表，转换为字符串
                processed_data[k] = norm_text(str(v))
            else:
                processed_data[k] = norm_text(str(v))
        ws.append(list(processed_data.values()))
    wb.save(file_path)
    logger.info(f'数据保存至 {file_path}')

def download_media(path, name, url, type):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://www.douyin.com/',
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }
    
    if type == 'image':
        try:
            res = requests.get(url, headers=headers, timeout=30)
            res.raise_for_status()
            with open(path + '/' + name + '.jpg', mode="wb") as f:
                f.write(res.content)
            logger.debug(f'图片下载成功: {name}.jpg')
        except Exception as e:
            logger.error(f'图片下载失败: {name}.jpg, 错误: {e}')
    elif type == 'video':
        try:
            res = requests.get(url, headers=headers, stream=True, timeout=30)
            res.raise_for_status()
            size = 0
            chunk_size = 1024 * 1024
            with open(path + '/' + name + '.mp4', mode="wb") as f:
                for data in res.iter_content(chunk_size=chunk_size):
                    if data:
                        f.write(data)
                        size += len(data)
            logger.debug(f'视频下载成功: {name}.mp4, 大小: {size} bytes')
        except Exception as e:
            logger.error(f'视频下载失败: {name}.mp4, 错误: {e}')
            # 创建一个空文件作为占位符
            with open(path + '/' + name + '.mp4', mode="wb") as f:
                f.write(b'')


def save_wrok_detail(work, path):
    with open(f'{path}/detail.txt', mode="w", encoding="utf-8") as f:
        # 逐行输出到txt里
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
        f.write(f"图片地址url列表: {', '.join(work['images'])}\n")
        f.write(f"标签: {', '.join(work['topics'])}\n")
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


@retry(tries=3, delay=1)
def download_work(work_info, path, save_choice):
    work_id = work_info['work_id']
    user_id = work_info['user_id']
    title = work_info['title']
    title = norm_str(title)[:40]
    nickname = work_info['nickname']
    nickname = norm_str(nickname)[:20]
    if title.strip() == '':
        title = f'无标题'
    
    # 使用os.path.join来构建路径，避免特殊字符问题
    save_path = os.path.join(path, f'{nickname}_{user_id}', f'{title}_{work_id}')
    check_and_create_path(save_path)
    with open(f'{save_path}/info.json', mode='w', encoding='utf-8') as f:
        f.write(json.dumps(work_info) + '\n')
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
        
        if video_cover and video_cover != '未知':
            download_media(save_path, 'cover', video_cover, 'image')
        if video_addr and video_addr != '未知':
            download_media(save_path, 'video', video_addr, 'video')
    logger.info(f'作品 {work_info["work_id"]} 下载完成，保存路径: {save_path}')
    return save_path



def check_and_create_path(path):
    if not os.path.exists(path):
        try:
            os.makedirs(path, exist_ok=True)
        except Exception as e:
            logger.error(f"创建路径失败: {path}, 错误: {e}")
            raise
