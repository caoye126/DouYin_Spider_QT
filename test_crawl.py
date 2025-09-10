# coding=utf-8
"""
测试爬取功能
作者：五更琉璃
日期：2025年
"""

import os
import sys
from utils.common_util import init
from main import Data_Spider

def test_crawl_with_error_handling():
    """测试爬取功能并详细处理错误"""
    try:
        print("开始测试爬取功能...")
        
        # 初始化
        auth, base_path = init()
        print(f"初始化成功，基础路径: {base_path}")
        
        # 创建爬虫实例
        data_spider = Data_Spider()
        print("爬虫实例创建成功")
        
        # 测试URL
        test_url = "https://www.douyin.com/video/1234567890"
        print(f"测试URL: {test_url}")
        
        # 检查认证信息
        if not auth:
            print("错误: 认证对象为空")
            return False
            
        if not hasattr(auth, 'cookie') or not auth.cookie:
            print("错误: Cookie为空，请检查.env文件配置")
            return False
            
        print(f"Cookie信息: {list(auth.cookie.keys()) if auth.cookie else '无'}")
        
        # 尝试爬取
        print("开始爬取...")
        work_info = data_spider.spider_work(auth, test_url)
        print(f"爬取成功: {work_info}")
        return True
        
    except Exception as e:
        print(f"爬取失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 检查是否是特定错误
        error_str = str(e)
        if "s_v_web_id" in error_str:
            print("提示: 这是Cookie配置问题，请检查.env文件中的DOUYIN_COOKIE")
        elif "目录名称无效" in error_str:
            print("提示: 这是路径问题，可能是文件名包含特殊字符")
        elif "WinError 267" in error_str:
            print("提示: 这是Windows路径错误，可能是路径中包含非法字符")
        
        return False

if __name__ == '__main__':
    print("="*50)
    print("抖音爬虫爬取测试")
    print("="*50)
    
    test_crawl_with_error_handling()
    
    print("\n测试完成!")
