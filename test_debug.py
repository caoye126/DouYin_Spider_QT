# coding=utf-8
"""
调试测试程序
作者：五更琉璃
日期：2025年
"""

import os
import sys
from utils.common_util import init

def test_init():
    """测试初始化功能"""
    try:
        print("开始测试初始化...")
        auth, base_path = init()
        print(f"初始化成功!")
        print(f"认证对象: {auth}")
        print(f"基础路径: {base_path}")
        return True
    except Exception as e:
        print(f"初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_path_creation():
    """测试路径创建"""
    try:
        print("开始测试路径创建...")
        import tempfile
        temp_dir = tempfile.gettempdir()
        test_path = os.path.join(temp_dir, 'douyin_spider', 'test')
        print(f"测试路径: {test_path}")
        os.makedirs(test_path, exist_ok=True)
        print("路径创建成功!")
        return True
    except Exception as e:
        print(f"路径创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_crawl():
    """测试简单爬取"""
    try:
        print("开始测试简单爬取...")
        auth, base_path = init()
        
        # 测试简单的数据获取
        from dy_apis.douyin_api import DouyinAPI
        print("API模块导入成功")
        
        # 测试一个简单的URL
        test_url = "https://www.douyin.com/video/1234567890"
        print(f"测试URL: {test_url}")
        
        # 这里不实际调用API，只是测试模块
        print("模块测试完成")
        return True
    except Exception as e:
        print(f"简单爬取测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("="*50)
    print("抖音爬虫调试测试")
    print("="*50)
    
    # 测试1: 路径创建
    print("\n1. 测试路径创建")
    test_path_creation()
    
    # 测试2: 初始化
    print("\n2. 测试初始化")
    test_init()
    
    # 测试3: 简单爬取
    print("\n3. 测试简单爬取")
    test_simple_crawl()
    
    print("\n测试完成!")
