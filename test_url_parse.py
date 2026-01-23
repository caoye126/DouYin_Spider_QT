#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试URL解析"""

url1 = 'https://www.douyin.com/user/MS4wLjABAAAAfAZC3mRZ_-1WHxtgYuQo-eAU8L3m-9o24XKmbtpyltc'
url2 = 'https://www.douyin.com/user/MS4wLjABAAAAfAZC3mRZ_-1WHxtgYuQo-eAU8L3m-9o24XKmbtpyltc?from_tab_name=main&is_search=0&list_name=follow&nt=0'

user_id1 = url1.split('/')[-1].split('?')[0]
user_id2 = url2.split('/')[-1].split('?')[0]

print(f'URL1: {url1}')
print(f'提取的用户ID: {user_id1}')
print(f'\nURL2: {url2}')
print(f'提取的用户ID: {user_id2}')
print(f'\n相同吗？ {user_id1 == user_id2}')

# 检查URL合法性
def normalize_user_url(url):
    """标准化用户URL，确保末尾没有查询参数"""
    if not url:
        return None
    
    # 移除末尾的空格
    url = url.strip()
    
    # 提取用户ID
    user_id = url.split('/')[-1].split('?')[0]
    
    # 检查用户ID是否为空
    if not user_id:
        return None
    
    # 返回标准化的URL
    return f'https://www.douyin.com/user/{user_id}'

url1_normalized = normalize_user_url(url1)
url2_normalized = normalize_user_url(url2)

print(f'\n标准化后的URL1: {url1_normalized}')
print(f'标准化后的URL2: {url2_normalized}')
print(f'标准化后相同吗？ {url1_normalized == url2_normalized}')
