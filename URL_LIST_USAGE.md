#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
URL列表配置功能说明
"""

功能说明：
==========

使用url_list文件批量下载作品，无需手动重复输入URL。


如何使用：
=========

1. 【创建配置文件】
   - 路径：datas/url_list
   - 文件格式：纯文本，每行一个URL
   - 注意：只识别以 https:// 或 http:// 开头的行
   - 其他行（包括注释）会被忽略

2. 【添加URL】
   打开 datas/url_list 文件，按以下格式添加：
   
   # 这是注释，会被忽略
   https://www.douyin.com/video/7376449060384935209
   https://www.douyin.com/video/7376449060384935210
   https://www.douyin.com/user/MS4wLjABAAAAfAZC3mRZ_-1WHxtgYuQo-eAU8L3m-9o24XKmbtpyltc
   
   不包含 https:// 的行会被忽略：
   just some random text

3. 【运行程序】
   - 启动"爬取单个视频"或"爬取用户所有作品"功能
   - 程序会自动检查url_list文件
   - 如果找到有效URL，使用文件中的URL
   - 如果未找到或文件不存在，提示手动输入URL

4. 【批量处理】
   - 程序会逐个处理url_list中的所有URL
   - 每个URL前显示进度：【1/10】、【2/10】等
   - 处理失败的URL会记录到日志，继续处理下一个


工作流程：
=========

【爬取单个视频】
  ↓
检查 datas/url_list 文件
  ├─ 文件存在且包含有效URL
  │   ↓
  │ 自动使用文件中的所有URL
  │   ↓
  │ 【1/n】处理视频 URL1
  │ 【2/n】处理视频 URL2
  │ ...
  │
  └─ 文件不存在或无有效URL
      ↓
    提示手动输入URL
      ↓
    处理用户输入的URL

【爬取用户所有作品】
  类似的流程，但处理用户主页URL


URL格式要求：
=============

视频URL：
  - https://www.douyin.com/video/7376449060384935209
  - https://www.douyin.com/video/7376449060384935209?xxx=yyy（带参数也可以）

用户主页URL：
  - https://www.douyin.com/user/MS4wLjABAAAAfAZC3mRZ_-1WHxtgYuQo-eAU8L3m-9o24XKmbtpyltc
  - https://www.douyin.com/user/MS4wLjABAAAAfAZC3mRZ_-1WHxtgYuQo-eAU8L3m-9o24XKmbtpyltc?xxx=yyy


日志记录：
=========

程序会记录：
  ✓ 从url_list文件中读取到N个URL
  ✓ 正在处理URL 1/N: <URL>
  ✓ 处理完成/处理失败信息

所有操作都会写入日志文件。


示例url_list文件：
==================

# 视频URL列表
https://www.douyin.com/video/7376449060384935209
https://www.douyin.com/video/7376449060384935210
https://www.douyin.com/video/7376449060384935211

# 用户主页URL列表
https://www.douyin.com/user/MS4wLjABAAAAfAZC3mRZ_-1WHxtgYuQo-eAU8L3m-9o24XKmbtpyltc
https://www.douyin.com/user/MS4wLjABAAAA99bTJ_GOw3odYmsXOe7i7xuEv0iQf2X_Kg_VUyVP0U8


注意事项：
=========

1. URL必须以 https:// 或 http:// 开头
2. 每行一个URL，多余空格会被自动删除
3. 空行和注释行（不以http开头）会被忽略
4. 文件编码必须是UTF-8
5. 如果url_list文件不存在，程序会提示手动输入URL
6. 如果url_list文件存在但无有效URL，也会提示手动输入

优势：
======

✓ 无需重复输入URL
✓ 支持批量处理
✓ 进度显示清晰
✓ 错误不中断处理
✓ 完整的日志记录
