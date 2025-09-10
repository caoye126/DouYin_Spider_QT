# coding=utf-8
"""
测试视频下载功能
作者：五更琉璃
日期：2025年
"""

import os
import requests
from utils.data_util import download_media

def test_video_download():
    """测试视频下载功能"""
    # 从info.json中获取视频URL
    info_file = "datas/media_datas/辰羊游戏_dyqhcr28pjv6/我的世界史蒂夫文明纯享版！一口气看完！#游戏#史蒂夫#我的世界#我的世界中国版#_7530155127756311834/info.json"
    
    if not os.path.exists(info_file):
        print("信息文件不存在")
        return
    
    import json
    with open(info_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    video_url = data.get('video_addr')
    if not video_url:
        print("没有找到视频URL")
        return
    
    print(f"视频URL: {video_url}")
    
    # 测试直接下载
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://www.douyin.com/',
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }
    
    try:
        print("开始测试视频下载...")
        res = requests.get(video_url, headers=headers, stream=True, timeout=30)
        print(f"响应状态码: {res.status_code}")
        print(f"响应头: {dict(res.headers)}")
        
        if res.status_code == 200:
            # 获取文件大小
            content_length = res.headers.get('content-length')
            if content_length:
                print(f"文件大小: {int(content_length)} bytes")
            
            # 下载前1MB测试
            test_size = 1024 * 1024  # 1MB
            downloaded = 0
            with open('test_video.mp4', 'wb') as f:
                for chunk in res.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if downloaded >= test_size:
                            break
            
            print(f"测试下载完成，下载了 {downloaded} bytes")
            
            # 检查文件内容
            with open('test_video.mp4', 'rb') as f:
                content = f.read(100)  # 读取前100字节
                print(f"文件开头内容: {content}")
                
        else:
            print(f"下载失败，状态码: {res.status_code}")
            print(f"响应内容: {res.text[:500]}")
            
    except Exception as e:
        print(f"下载出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_video_download()
