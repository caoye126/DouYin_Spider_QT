import os
# from loguru import logger
from dotenv import load_dotenv

dy_auth = None
dy_live_auth = None
def load_env():
    global dy_auth, dy_live_auth
    load_dotenv()
    cookies_dy = os.getenv('DOUYIN_COOKIE')
    cookies_live = os.getenv('LIVE_COOKIE')
    
    # 检查Cookie是否配置
    if not cookies_dy or cookies_dy == 'your_douyin_cookie_here':
        print("警告: 未配置DOUYIN_COOKIE，请编辑.env文件")
        cookies_dy = ""
    
    if not cookies_live or cookies_live == 'your_live_cookie_here':
        print("警告: 未配置LIVE_COOKIE，请编辑.env文件")
        cookies_live = ""
    
    from builder.auth import DouyinAuth
    dy_auth = DouyinAuth()
    dy_auth.perepare_auth(cookies_dy, "", "")
    dy_live_auth = DouyinAuth()
    dy_live_auth.perepare_auth(cookies_live, "", "")
    return dy_auth

def init():
    # 使用项目目录保存数据
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    media_base_path = os.path.join(project_root, 'datas', 'media_datas')
    excel_base_path = os.path.join(project_root, 'datas', 'excel_datas')
    
    try:
        os.makedirs(media_base_path, exist_ok=True)
        os.makedirs(excel_base_path, exist_ok=True)
        print(f'数据目录: {media_base_path}')
        print(f'Excel目录: {excel_base_path}')
    except Exception as e:
        print(f'创建目录失败: {e}')
        # 如果还是失败，使用当前目录
        media_base_path = 'media_datas'
        excel_base_path = 'excel_datas'
        os.makedirs(media_base_path, exist_ok=True)
        os.makedirs(excel_base_path, exist_ok=True)
    
    cookies = load_env()
    base_path = {
        'media': media_base_path,
        'excel': excel_base_path,
    }
    return cookies, base_path
