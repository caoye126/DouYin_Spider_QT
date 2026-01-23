# coding=utf-8
"""
抖音爬虫主程序
作者：五更琉璃
日期：2025年
"""

import json
import os
from loguru import logger

from dy_apis.douyin_api import DouyinAPI
from utils.common_util import init
from utils.data_util import handle_work_info, download_work, save_to_xlsx


class Data_Spider():
    def __init__(self):
        self.douyin_apis = DouyinAPI()
        # 初始化认证信息
        self.auth, self.base_path = init()

    def spider_work(self, auth, work_url: str, proxies=None):
        """
        爬取一个作品的信息
        :param auth : 用户认证信息
        :param work_url: 作品链接
        :return:
        """
        res_json = self.douyin_apis.get_work_info(auth, work_url)
        data = res_json['aweme_detail']

        work_info = handle_work_info(data)
        logger.info(f'爬取作品信息 {work_url}')
        return work_info

    def spider_some_work(self, auth, works: list, base_path: dict, save_choice: str, excel_name: str = '', proxies=None):
        """
        爬取一些作品的信息
        :param auth: 用户认证信息
        :param works: 作品链接列表
        :param base_path: 保存路径
        :param save_choice: 保存方式 all: 保存所有的信息, media: 保存视频和图片（media-video只下载视频, media-image只下载图片，media都下载）, excel: 保存到excel
        :param excel_name: excel文件名
        :return:
        """
        if (save_choice == 'all' or save_choice == 'excel') and excel_name == '':
            raise ValueError('excel_name 不能为空')
        work_list = []
        total_works = len(works)
        for work_url in works:
            work_info = self.spider_work(auth, work_url)
            work_list.append(work_info)
        for idx, work_info in enumerate(work_list, 1):
            if save_choice == 'all' or 'media' in save_choice:
                logger.info(f'正在下载作品 {idx}/{total_works}')
                download_work(work_info, base_path['media'], save_choice)
        if save_choice == 'all' or save_choice == 'excel':
            file_path = os.path.abspath(os.path.join(base_path['excel'], f'{excel_name}.xlsx'))
            save_to_xlsx(work_list, file_path)


    def spider_user_all_work(self, auth, user_url: str, base_path: dict, save_choice: str, excel_name: str = '', proxies=None):
        """
        爬取一个用户的所有作品
        :param auth: 用户认证信息
        :param user_url: 用户链接
        :param base_path: 保存路径
        :param save_choice: 保存方式 all: 保存所有的信息, media: 保存视频和图片（media-video只下载视频, media-image只下载图片，media都下载）, excel: 保存到excel
        :param excel_name: excel文件名
        :param proxies: 代理
        :return:
        """
        user_info = self.douyin_apis.get_user_info(auth, user_url)
        work_list = self.douyin_apis.get_user_all_work_info(auth, user_url)
        work_info_list = []
        total_works = len(work_list)
        logger.info(f'用户 {user_url} 作品数量: {total_works}')
        if save_choice == 'all' or save_choice == 'excel':
            excel_name = user_url.split('/')[-1].split('?')[0]

        for idx, work_info in enumerate(work_list, 1):
            work_info['author'].update(user_info['user'])
            work_info = handle_work_info(work_info)
            work_info_list.append(work_info)
            logger.info(f'爬取作品信息 {work_info["work_url"]}')
            if save_choice == 'all' or 'media' in save_choice:
                logger.info(f'正在下载作品 {idx}/{total_works}')
                download_work(work_info, base_path['media'], save_choice)
        if save_choice == 'all' or save_choice == 'excel':
            file_path = os.path.abspath(os.path.join(base_path['excel'], f'{excel_name}.xlsx'))
            save_to_xlsx(work_info_list, file_path)

    def spider_some_search_work(self, auth, query: str, require_num: int, base_path: dict, save_choice: str,  sort_type: str, publish_time: str, filter_duration="", search_range="", content_type="",   excel_name: str = '', proxies=None):
        """
            :param auth: DouyinAuth object.
            :param query: 搜索关键字.
            :param require_num: 搜索结果数量.
            :param base_path: 保存路径.
            :param save_choice: 保存方式 all: 保存所有的信息, media: 保存视频和图片（media-video只下载视频, media-image只下载图片，media都下载）, excel: 保存到excel
            :param sort_type: 排序方式 0 综合排序, 1 最多点赞, 2 最新发布.
            :param publish_time: 发布时间 0 不限, 1 一天内, 7 一周内, 180 半年内.
            :param filter_duration: 视频时长 空字符串 不限, 0-1 一分钟内, 1-5 1-5分钟内, 5-10000 5分钟以上
            :param search_range: 搜索范围 0 不限, 1 最近看过, 2 还未看过, 3 关注的人
            :param content_type: 内容形式 0 不限, 1 视频, 2 图文
            :param excel_name: excel文件名
        """
        work_info_list = []
        work_list = self.douyin_apis.search_some_general_work(auth, query, require_num, sort_type, publish_time, filter_duration, search_range, content_type)
        total_works = len(work_list)
        logger.info(f'搜索关键词 {query} 作品数量: {total_works}')
        if save_choice == 'all' or save_choice == 'excel':
            excel_name = query
        for idx, work_info in enumerate(work_list, 1):
            logger.info(json.dumps(work_info))
            logger.info(f'爬取作品信息 https://www.douyin.com/video/{work_info["aweme_info"]["aweme_id"]}')
            work_info = handle_work_info(work_info['aweme_info'])
            work_info_list.append(work_info)
            if save_choice == 'all' or 'media' in save_choice:
                logger.info(f'正在下载作品 {idx}/{total_works}')
                download_work(work_info, base_path['media'], save_choice)
        if save_choice == 'all' or save_choice == 'excel':
            file_path = os.path.abspath(os.path.join(base_path['excel'], f'{excel_name}.xlsx'))
            save_to_xlsx(work_info_list, file_path)
    
    def spider_work_simple(self, work_url: str, proxies=None):
        """
        爬取一个作品的信息（适配Qt界面）
        :param work_url: 作品链接
        :return: 作品信息
        """
        res_json = self.douyin_apis.get_work_info(self.auth, work_url)
        data = res_json['aweme_detail']
        
        # 返回原始数据和处理后的数据
        processed_info = handle_work_info(data)
        processed_info['raw_data'] = data  # 保存原始数据用于下载
        
        logger.info(f'爬取作品信息 {work_url}')
        return processed_info
    
    def spider_user_all_work_simple(self, user_url: str, proxies=None):
        """
        爬取一个用户的所有作品（适配Qt界面）
        :param user_url: 用户链接
        :return: 作品列表
        """
        # 规范化用户URL
        from dy_apis.douyin_api import normalize_user_url
        user_url = normalize_user_url(user_url)
        
        user_info = self.douyin_apis.get_user_info(self.auth, user_url)
        work_list = self.douyin_apis.get_user_all_work_info(self.auth, user_url)
        work_info_list = []
        logger.info(f'用户 {user_url} 作品数量: {len(work_list)}')
        
        for work_info in work_list:
            work_info['author'].update(user_info['user'])
            processed_info = handle_work_info(work_info)
            processed_info['raw_data'] = work_info  # 保存原始数据用于下载
            work_info_list.append(processed_info)
            logger.info(f'爬取作品信息 {processed_info["work_url"]}')
        
        return work_info_list
    
    def spider_work_comments(self, work_url: str, proxies=None):
        """
        爬取视频评论（适配Qt界面）
        :param work_url: 作品链接
        :return: 评论列表
        """
        # 直接从URL中提取视频ID
        import re
        video_id = None
        
        # 方法1: 从modal_id参数中提取
        if 'modal_id=' in work_url:
            match = re.search(r'modal_id=(\d+)', work_url)
            if match:
                video_id = match.group(1)
        
        # 方法2: 从标准视频URL中提取
        if not video_id:
            match = re.search(r'/video/(\d+)', work_url)
            if match:
                video_id = match.group(1)
        
        if not video_id:
            raise ValueError("无法从URL中提取视频ID")
        
        # 获取评论
        standard_url = f"https://www.douyin.com/video/{video_id}"
        comments = self.douyin_apis.get_work_all_comment(self.auth, standard_url)
        return comments

    def spider_search_videos_simple(self, query: str, require_num: int, sort_type: str = "0", publish_time: str = "0", filter_duration: str = "", search_range: str = "", content_type: str = "", proxies=None):
        """
        搜索视频（适配Qt界面）
        :param query: 搜索关键词
        :param require_num: 搜索结果数量
        :param sort_type: 排序方式
        :param publish_time: 发布时间
        :param filter_duration: 视频时长
        :param search_range: 搜索范围
        :param content_type: 内容形式
        :return: 处理后的视频列表
        """
        work_list = self.douyin_apis.search_some_general_work(self.auth, query, require_num, sort_type, publish_time, filter_duration, search_range, content_type)
        logger.info(f'搜索关键词 {query} 作品数量: {len(work_list)}')
        
        processed_list = []
        for work_info in work_list:
            try:
                # 处理作品信息
                processed_info = handle_work_info(work_info['aweme_info'])
                processed_info['raw_data'] = work_info['aweme_info']  # 保存原始数据用于下载
                processed_list.append(processed_info)
                logger.info(f'爬取作品信息 https://www.douyin.com/video/{work_info["aweme_info"]["aweme_id"]}')
            except Exception as e:
                logger.error(f"处理作品信息失败: {e}")
                continue
        
        return processed_list

if __name__ == '__main__':
    """
        此文件为爬虫的入口文件，可以直接运行
        dy_apis/douyin_apis.py 为爬虫的api文件，包含抖音的全部数据接口，可以继续封装
        dy_live/server.py 为监听抖音直播的入口文件，可以直接运行
        作者：五更琉璃
        日期：2025年
    """
    
    import sys
    
    # 检查是否使用控制台界面或Qt界面
    if len(sys.argv) > 1:
        if sys.argv[1] == '--console':
            from console_interface import ConsoleInterface
            interface = ConsoleInterface()
            interface.run()
        elif sys.argv[1] == '--qt':
            from qt_interface import main as qt_main
            qt_main()
        else:
            print("未知参数，使用默认模式")
            print("可用参数:")
            print("  --console: 启动控制台界面")
            print("  --qt: 启动Qt图形界面")
    else:
        # 原有的示例代码
        auth, base_path = init()
        data_spider = Data_Spider()
        
        print("抖音爬虫示例运行")
        print("如需使用交互式控制台，请运行: python main.py --console")
        print("="*50)
        
        # 示例：爬取单个视频
        try:
            # 示例视频URL（请替换为有效的URL）
            video_url = 'https://www.douyin.com/video/7445533736877264178'
            print(f"正在爬取视频: {video_url}")
            work_info = data_spider.spider_work(auth, video_url)
            print(f"视频标题: {work_info.get('title', 'N/A')}")
            print(f"作者: {work_info.get('author', {}).get('nickname', 'N/A')}")
            print("爬取完成！")
        except Exception as e:
            print(f"示例运行失败: {e}")
            print("请检查网络连接和cookie配置")

