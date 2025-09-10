# coding=utf-8
"""
修复视频下载问题
作者：五更琉璃
日期：2025年
"""

import os
import json
import requests
from utils.data_util import download_media

def fix_video_downloads():
    """修复所有下载失败的视频文件"""
    base_path = "datas/media_datas/辰羊游戏_dyqhcr28pjv6"
    
    if not os.path.exists(base_path):
        print("数据目录不存在")
        return
    
    # 遍历所有视频文件夹
    for folder_name in os.listdir(base_path):
        folder_path = os.path.join(base_path, folder_name)
        if not os.path.isdir(folder_path):
            continue
        
        info_file = os.path.join(folder_path, "info.json")
        video_file = os.path.join(folder_path, "video.mp4")
        
        if not os.path.exists(info_file):
            continue
        
        # 检查视频文件大小
        if os.path.exists(video_file):
            file_size = os.path.getsize(video_file)
            if file_size > 1000:  # 如果文件大于1KB，跳过
                print(f"跳过 {folder_name}，文件大小正常: {file_size} bytes")
                continue
        
        print(f"修复视频: {folder_name}")
        
        # 读取视频信息
        try:
            with open(info_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            video_url = data.get('video_addr')
            if not video_url:
                print(f"  没有找到视频URL")
                continue
            
            # 重新下载视频
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://www.douyin.com/',
                'Accept': '*/*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
            }
            
            try:
                res = requests.get(video_url, headers=headers, stream=True, timeout=60)
                res.raise_for_status()
                
                size = 0
                chunk_size = 1024 * 1024
                with open(video_file, "wb") as f:
                    for data in res.iter_content(chunk_size=chunk_size):
                        if data:
                            f.write(data)
                            size += len(data)
                
                print(f"  下载完成，大小: {size} bytes")
                
            except Exception as e:
                print(f"  下载失败: {e}")
                
        except Exception as e:
            print(f"  处理失败: {e}")

if __name__ == '__main__':
    fix_video_downloads()
