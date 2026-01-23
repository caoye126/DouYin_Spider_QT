# coding=utf-8
"""
抖音爬虫控制台界面
作者：五更琉璃
日期：2025年
"""

import os
import sys
import threading
from loguru import logger

from dy_apis.douyin_api import DouyinAPI
from utils.common_util import init
from utils.data_util import handle_work_info, download_work, save_to_xlsx
from main import Data_Spider


class ConsoleInterface:
    """控制台界面类"""
    
    def __init__(self):
        """初始化控制台界面"""
        self.data_spider = Data_Spider()
        self.auth = None
        self.base_path = None
        self.user_input = None
        self.input_lock = threading.Lock()
    
    def get_user_input_with_timeout(self, prompt, input_type="str", timeout=0, default_value=None, allow_empty=False):
        """
        获取用户输入（支持超时）
        :param prompt: 提示信息
        :param input_type: 输入类型 (str, int, url)
        :param timeout: 超时时间（秒），0表示不超时
        :param default_value: 超时后的默认值
        :param allow_empty: 是否允许空输入
        :return: 用户输入或默认值
        """
        if timeout > 0 and default_value is not None:
            print(f"{prompt} (默认值: {default_value}, {timeout}秒后自动使用默认值): ", end="", flush=True)
            self.user_input = None
            
            def input_thread():
                try:
                    self.user_input = input()
                except:
                    pass
            
            thread = threading.Thread(target=input_thread, daemon=True)
            thread.start()
            thread.join(timeout=timeout)
            
            if self.user_input is None:
                print(f"\n(未输入，使用默认值: {default_value})")
                return default_value
            
            user_input = self.user_input.strip()
            
            # 验证输入
            if not user_input:
                if allow_empty:
                    return ""
                else:
                    print("输入不能为空，使用默认值")
                    return default_value
            
            # 类型转换
            if input_type == "int":
                try:
                    return int(user_input)
                except ValueError:
                    print(f"输入格式错误，使用默认值")
                    return default_value
            elif input_type == "url":
                if not (user_input.startswith("http://") or user_input.startswith("https://")):
                    print("请输入有效的URL地址，使用默认值")
                    return default_value
                return user_input
            else:
                return user_input
        else:
            # 无超时的普通输入
            return self.get_user_input(prompt, input_type, allow_empty)
    
    def init_auth(self):
        """初始化认证信息"""
        try:
            self.auth, self.base_path = init()
            logger.info("认证信息初始化成功")
            return True
        except Exception as e:
            logger.error(f"认证信息初始化失败: {e}")
            return False
    
    def display_menu(self):
        """显示主菜单"""
        print("\n" + "="*50)
        print("🎶 抖音爬虫控制台 - 五更琉璃")
        print("="*50)
        print("1. 爬取单个视频信息")
        print("2. 爬取用户所有作品")
        print("3. 搜索视频")
        print("4. 爬取视频评论区")
        print("5. 监听直播间")
        print("6. 搜索用户")
        print("7. 搜索直播间")
        print("0. 退出程序")
        print("="*50)
    
    def get_user_input(self, prompt, input_type="str", allow_empty=False):
        """获取用户输入"""
        while True:
            try:
                user_input = input(f"{prompt}: ").strip()
                
                # 如果允许空输入且用户输入为空，返回空字符串
                if allow_empty and not user_input:
                    return ""
                
                # 如果不允许空输入且用户输入为空，提示重新输入
                if not allow_empty and not user_input:
                    print("输入不能为空，请重新输入")
                    continue
                
                if input_type == "int":
                    return int(user_input)
                elif input_type == "url":
                    if not (user_input.startswith("http://") or user_input.startswith("https://")):
                        print("请输入有效的URL地址")
                        continue
                    return user_input
                else:
                    return user_input
            except ValueError:
                print("输入格式错误，请重新输入")
            except KeyboardInterrupt:
                print("\n程序已退出")
                sys.exit(0)
    
    def crawl_single_video(self):
        """爬取单个视频信息"""
        print("\n--- 爬取单个视频信息 ---")
        
        # 检查Cookie配置
        if not self.auth or not self.auth.cookie:
            print("错误: 未配置有效的Cookie，请编辑.env文件配置DOUYIN_COOKIE")
            return
        
        video_url = self.get_user_input("请输入视频URL", "url")
        
        try:
            work_info = self.data_spider.spider_work(self.auth, video_url)
            print(f"视频标题: {work_info.get('title', 'N/A')}")
            print(f"作者: {work_info.get('author', {}).get('nickname', 'N/A')}")
            print(f"点赞数: {work_info.get('statistics', {}).get('digg_count', 'N/A')}")
            print(f"评论数: {work_info.get('statistics', {}).get('comment_count', 'N/A')}")
            print(f"分享数: {work_info.get('statistics', {}).get('share_count', 'N/A')}")
            
            save_choice = self.get_user_input("是否保存数据？(all/media/excel/none)", "str").lower()
            if save_choice in ['all', 'media', 'excel']:
                excel_name = self.get_user_input("请输入保存文件名", "str") if save_choice in ['all', 'excel'] else 'single_video'
                self.data_spider.spider_some_work(self.auth, [video_url], self.base_path, save_choice, excel_name)
                print("数据保存成功！")
        except Exception as e:
            logger.error(f"爬取视频信息失败: {e}")
            print(f"爬取失败: {e}")
            if "s_v_web_id" in str(e):
                print("提示: 请检查.env文件中的DOUYIN_COOKIE配置是否正确")
            elif "jsrsasign" in str(e):
                print("提示: 缺少JavaScript依赖模块，请运行以下命令安装:")
                print("  npm install jsrsasign")
                print("  或者升级Node.js到20+版本")
            elif "Cannot find module" in str(e):
                print("提示: 缺少Node.js模块，请检查Node.js环境配置")
    
    def crawl_user_works(self):
        """爬取用户所有作品"""
        print("\n--- 爬取用户所有作品 ---")
        
        # 检查Cookie配置
        if not self.auth or not self.auth.cookie:
            print("错误: 未配置有效的Cookie，请编辑.env文件配置DOUYIN_COOKIE")
            return
        
        user_url = self.get_user_input("请输入用户主页URL", "url")
        
        try:
            # 保存方式处设置10秒超时，默认值为media
            save_choice = self.get_user_input_with_timeout(
                "保存方式 (all/media/excel)", 
                input_type="str", 
                timeout=10, 
                default_value="media"
            ).lower()
            self.data_spider.spider_user_all_work(self.auth, user_url, self.base_path, save_choice)
            print("用户作品爬取完成！")
        except Exception as e:
            logger.error(f"爬取用户作品失败: {e}")
            print(f"爬取失败: {e}")
            if "s_v_web_id" in str(e):
                print("提示: 请检查.env文件中的DOUYIN_COOKIE配置是否正确")
    
    def search_videos(self):
        """搜索视频"""
        print("\n--- 搜索视频 ---")
        
        # 检查Cookie配置
        if not self.auth or not self.auth.cookie:
            print("错误: 未配置有效的Cookie，请编辑.env文件配置DOUYIN_COOKIE")
            return
        
        query = self.get_user_input("请输入搜索关键词", "str")
        require_num = self.get_user_input("请输入要获取的视频数量", "int")
        
        print("\n排序方式:")
        print("0 - 综合排序")
        print("1 - 最多点赞")
        print("2 - 最新发布")
        sort_type = self.get_user_input("请选择排序方式 (0/1/2)", "str")
        
        print("\n发布时间:")
        print("0 - 不限")
        print("1 - 一天内")
        print("7 - 一周内")
        print("180 - 半年内")
        publish_time = self.get_user_input("请选择发布时间 (0/1/7/180)", "str")
        
        print("\n视频时长:")
        print("空 - 不限")
        print("0-1 - 一分钟内")
        print("1-5 - 1-5分钟内")
        print("5-10000 - 5分钟以上")
        filter_duration = self.get_user_input("请选择视频时长 (直接回车为不限)", "str", allow_empty=True)
        
        try:
            save_choice = self.get_user_input("保存方式 (all/media/excel)", "str").lower()
            self.data_spider.spider_some_search_work(
                self.auth, query, require_num, self.base_path, save_choice, 
                sort_type, publish_time, filter_duration, "0", "0"
            )
            print("视频搜索完成！")
        except Exception as e:
            logger.error(f"搜索视频失败: {e}")
            print(f"搜索失败: {e}")
            if "s_v_web_id" in str(e):
                print("提示: 请检查.env文件中的DOUYIN_COOKIE配置是否正确")
    
    def crawl_video_comments(self):
        """爬取视频评论区"""
        print("\n--- 爬取视频评论区 ---")
        video_url = self.get_user_input("请输入视频URL", "url")
        
        try:
            # 获取视频信息
            work_info = self.data_spider.spider_work(self.auth, video_url)
            print(f"正在爬取视频 '{work_info.get('title', 'N/A')}' 的评论区...")
            
            # 尝试多次爬取评论，增加重试机制
            max_retries = 3
            all_comments = []
            
            for attempt in range(max_retries):
                try:
                    print(f"尝试第 {attempt + 1} 次爬取...")
                    all_comments = self.data_spider.douyin_apis.get_work_all_comment(self.auth, video_url)
                    
                    if all_comments:
                        print(f"✅ 成功获取 {len(all_comments)} 条评论")
                        break
                    else:
                        print(f"第 {attempt + 1} 次尝试未获取到评论数据")
                        
                except Exception as e:
                    print(f"第 {attempt + 1} 次尝试失败: {str(e)[:100]}...")
                    if attempt < max_retries - 1:
                        print("等待3秒后重试...")
                        import time
                        time.sleep(3)
                    else:
                        print("所有重试都失败了")
                        raise e
            
            if not all_comments:
                print("❌ 未找到评论数据，可能的原因：")
                print("1. 网络连接不稳定")
                print("2. 视频没有评论")
                print("3. 抖音服务器限制")
                print("4. Cookie配置问题")
                return
            
            print(f"\n📝 评论详情:")
            
            # 显示前几条评论
            for i, comment in enumerate(all_comments[:5]):
                print(f"\n评论 {i+1}:")
                print(f"用户: {comment.get('user', {}).get('nickname', 'N/A')}")
                print(f"内容: {comment.get('text', 'N/A')}")
                print(f"点赞数: {comment.get('digg_count', 'N/A')}")
                if comment.get('reply_comment'):
                    print(f"回复数: {len(comment['reply_comment'])}")
            
            if len(all_comments) > 5:
                print(f"\n... 还有 {len(all_comments) - 5} 条评论")
            
            # 自动保存评论到文件
            try:
                import json
                import os
                from datetime import datetime
                
                # 创建保存目录
                save_dir = os.path.join(os.getcwd(), 'datas', 'comments')
                os.makedirs(save_dir, exist_ok=True)
                
                # 生成文件名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"comments_{work_info.get('aweme_id', 'unknown')}_{timestamp}.json"
                filepath = os.path.join(save_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(all_comments, f, ensure_ascii=False, indent=2)
                print(f"📁 评论数据已自动保存到: {filepath}")
                
            except Exception as save_error:
                print(f"保存评论数据失败: {save_error}")
                
        except Exception as e:
            logger.error(f"爬取视频评论失败: {e}")
            print(f"❌ 爬取失败: {e}")
            print("\n💡 建议解决方案：")
            print("1. 检查网络连接是否稳定")
            print("2. 尝试使用不同的视频URL")
            print("3. 检查Cookie配置是否正确")
            print("4. 稍后再试")
    
    def monitor_live_room(self):
        """监听直播间"""
        print("\n--- 监听直播间 ---")
        
        # 检查Cookie配置
        if not self.auth or not self.auth.cookie:
            print("错误: 未配置有效的Cookie，请编辑.env文件配置LIVE_COOKIE")
            return
        
        live_id = self.get_user_input("请输入直播间ID", "str")
        
        try:
            # 检查直播间状态
            live_info = self.data_spider.douyin_apis.get_live_info(self.auth, live_id)
            if live_info:
                print(f"直播间标题: {live_info.get('room_title', 'N/A')}")
                print(f"直播间状态: {'直播中' if live_info.get('room_status') == '2' else '未开播'}")
                
                if live_info.get('room_status') == '2':
                    print("开始监听直播间...")
                    # 这里可以调用直播监听功能
                    try:
                        from dy_live.server import start_live_monitor
                        start_live_monitor(live_id)
                    except ImportError:
                        print("直播监听模块未正确配置")
                else:
                    print("直播间当前未开播")
            else:
                print("无法获取直播间信息")
        except Exception as e:
            logger.error(f"监听直播间失败: {e}")
            print(f"监听失败: {e}")
            if "ttwid" in str(e):
                print("提示: 请检查.env文件中的LIVE_COOKIE配置是否正确")
    
    def search_users(self):
        """搜索用户"""
        print("\n--- 搜索用户 ---")
        query = self.get_user_input("请输入搜索关键词", "str")
        require_num = self.get_user_input("请输入要获取的用户数量", "int")
        
        try:
            users = self.data_spider.douyin_apis.search_some_user(self.auth, query, require_num)
            print(f"找到 {len(users)} 个用户:")
            
            # 保存数据到文件
            import json
            import os
            from datetime import datetime
            
            # 创建保存目录
            save_dir = os.path.join(os.getcwd(), 'datas', 'user_search_results')
            os.makedirs(save_dir, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"user_search_{query}_{timestamp}.json"
            filepath = os.path.join(save_dir, filename)
            
            # 保存原始数据
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(users, f, ensure_ascii=False, indent=2)
            
            print(f"原始数据已保存到: {filepath}")
            
            # 处理并显示数据
            processed_data = []
            for i, user in enumerate(users[:require_num]):  # 显示用户要求的数量
                # 尝试不同的数据结构路径
                user_info = user.get('user_info', {})
                if not user_info and isinstance(user, dict):
                    # 如果 'user_info' 键不存在，直接使用 user 作为 user_info
                    user_info = user
                
                # 安全获取用户信息
                nickname = user_info.get('nickname', 'N/A')
                follower_count = user_info.get('follower_count', 'N/A')
                following_count = user_info.get('following_count', 'N/A')
                total_favorited = user_info.get('total_favorited', 'N/A')
                aweme_count = user_info.get('aweme_count', 'N/A')
                sec_uid = user_info.get('sec_uid', 'N/A')
                uid = user_info.get('uid', 'N/A')
                signature = user_info.get('signature', 'N/A')
                avatar_url = user_info.get('avatar_thumb', {}).get('url_list', ['N/A'])[0] if user_info.get('avatar_thumb') else 'N/A'
                
                # 构建用户主页链接
                if sec_uid and sec_uid != 'N/A':
                    user_url = f"https://www.douyin.com/user/{sec_uid}"
                elif uid and uid != 'N/A':
                    user_url = f"https://www.douyin.com/user/{uid}"
                else:
                    user_url = 'N/A'
                
                # 格式化数字显示
                def format_number(num):
                    if num == 'N/A' or num is None:
                        return 'N/A'
                    try:
                        num = int(num)
                        if num >= 10000:
                            return f"{num/10000:.1f}万"
                        else:
                            return str(num)
                    except:
                        return str(num)
                
                print(f"\n用户 {i+1}:")
                print(f"昵称: {nickname}")
                print(f"粉丝数: {format_number(follower_count)}")
                print(f"关注数: {format_number(following_count)}")
                print(f"获赞数: {format_number(total_favorited)}")
                print(f"作品数: {format_number(aweme_count)}")
                print(f"个人简介: {signature}")
                print(f"用户主页: {user_url}")
                print(f"头像链接: {avatar_url}")
                
                # 保存处理后的数据
                processed_data.append({
                    'index': i + 1,
                    'nickname': nickname,
                    'follower_count': follower_count,
                    'following_count': following_count,
                    'total_favorited': total_favorited,
                    'aweme_count': aweme_count,
                    'signature': signature,
                    'user_url': user_url,
                    'avatar_url': avatar_url,
                    'sec_uid': sec_uid,
                    'uid': uid
                })
            
            # 保存处理后的数据到Excel
            try:
                import pandas as pd
                df = pd.DataFrame(processed_data)
                excel_filename = f"user_search_{query}_{timestamp}.xlsx"
                excel_filepath = os.path.join(save_dir, excel_filename)
                df.to_excel(excel_filepath, index=False, engine='openpyxl')
                print(f"📊 Excel数据已保存到: {excel_filepath}")
            except Exception as e:
                print(f"保存Excel失败: {e}")
            
            print(f"\n✅ 搜索完成！找到 {len(users)} 个用户")
            print(f"📁 原始数据已保存到: {filepath}")
            print(f"📊 处理后的数据已保存到Excel文件")
                
        except Exception as e:
            logger.error(f"搜索用户失败: {e}")
            print(f"搜索失败: {e}")
            if "s_v_web_id" in str(e):
                print("提示: 请检查.env文件中的DOUYIN_COOKIE配置是否正确")
    
    def search_live_rooms(self):
        """搜索直播间"""
        print("\n--- 搜索直播间 ---")
        query = self.get_user_input("请输入搜索关键词", "str")
        require_num = self.get_user_input("请输入要获取的直播间数量", "int")
        
        try:
            lives = self.data_spider.douyin_apis.search_some_live(self.auth, query, require_num)
            print(f"找到 {len(lives)} 个直播间:")
            
            # 保存数据到文件
            import json
            import os
            from datetime import datetime
            
            # 创建保存目录
            save_dir = os.path.join(os.getcwd(), 'datas', 'live_search_results')
            os.makedirs(save_dir, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"live_search_{query}_{timestamp}.json"
            filepath = os.path.join(save_dir, filename)
            
            # 保存原始数据
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(lives, f, ensure_ascii=False, indent=2)
            
            print(f"原始数据已保存到: {filepath}")
            
            # 处理并显示数据
            processed_data = []
            for i, live in enumerate(lives[:require_num]):  # 显示用户要求的数量
                # 根据实际数据结构解析
                live_info = live.get('lives', {})
                author_info = live_info.get('author', {})
                
                # 从rawdata中解析更多信息
                rawdata = live_info.get('rawdata', '{}')
                try:
                    import json
                    rawdata_dict = json.loads(rawdata) if isinstance(rawdata, str) else rawdata
                except:
                    rawdata_dict = {}
                
                # 获取基本信息
                title = rawdata_dict.get('title', live_info.get('title', 'N/A'))
                user_count = rawdata_dict.get('user_count', live_info.get('user_count_str', 'N/A'))
                web_rid = rawdata_dict.get('id_str', live_info.get('web_rid', 'N/A'))
                nickname = author_info.get('nickname', 'N/A')
                sec_uid = author_info.get('sec_uid', 'N/A')
                
                # 构建直播间链接
                if web_rid and web_rid != 'N/A':
                    live_url = f"https://live.douyin.com/{web_rid}"
                else:
                    live_url = 'N/A'
                
                # 构建主播主页链接
                if sec_uid and sec_uid != 'N/A':
                    user_url = f"https://www.douyin.com/user/{sec_uid}"
                else:
                    user_url = 'N/A'
                
                # 获取状态信息
                status = rawdata_dict.get('status', live_info.get('status', 'N/A'))
                if status == 2:
                    status = '直播中'
                elif status == 1:
                    status = '未开播'
                else:
                    status = f'状态{status}'
                
                # 获取更多信息
                create_time = rawdata_dict.get('create_time', 'N/A')
                owner_user_id = rawdata_dict.get('owner_user_id', 'N/A')
                
                print(f"\n直播间 {i+1}:")
                print(f"主播: {nickname}")
                print(f"标题: {title}")
                print(f"观看人数: {user_count}")
                print(f"直播间ID: {web_rid}")
                print(f"直播间链接: {live_url}")
                print(f"状态: {status}")
                print(f"主播主页: {user_url}")
                print(f"创建时间: {create_time}")
                print(f"主播ID: {owner_user_id}")
                
                # 保存处理后的数据
                processed_data.append({
                    'index': i + 1,
                    'nickname': nickname,
                    'title': title,
                    'user_count': user_count,
                    'web_rid': web_rid,
                    'live_url': live_url,
                    'status': status,
                    'user_url': user_url,
                    'create_time': create_time,
                    'owner_user_id': owner_user_id,
                    'sec_uid': sec_uid
                })
            
            # 保存处理后的数据到Excel
            try:
                import pandas as pd
                df = pd.DataFrame(processed_data)
                excel_filename = f"live_search_{query}_{timestamp}.xlsx"
                excel_filepath = os.path.join(save_dir, excel_filename)
                df.to_excel(excel_filepath, index=False, engine='openpyxl')
                print(f"📊 Excel数据已保存到: {excel_filepath}")
            except Exception as e:
                print(f"保存Excel失败: {e}")
            
            print(f"\n✅ 搜索完成！找到 {len(lives)} 个直播间")
            print(f"📁 原始数据已保存到: {filepath}")
            print(f"📊 处理后的数据已保存到Excel文件")
            
        except Exception as e:
            print(f"搜索失败: {e}")
            import traceback
            traceback.print_exc()
    
    def run(self):
        """运行控制台界面"""
        print("正在初始化抖音爬虫...")
        
        if not self.init_auth():
            print("初始化失败，请检查.env文件配置")
            return
        
        while True:
            try:
                self.display_menu()
                # 菜单选项处设置10秒超时，默认值为2
                choice = self.get_user_input_with_timeout(
                    "请选择功能 (0-7)", 
                    input_type="str", 
                    timeout=10, 
                    default_value="2"
                )
                
                if choice == "0":
                    print("感谢使用抖音爬虫！")
                    break
                elif choice == "1":
                    self.crawl_single_video()
                elif choice == "2":
                    self.crawl_user_works()
                elif choice == "3":
                    self.search_videos()
                elif choice == "4":
                    self.crawl_video_comments()
                elif choice == "5":
                    self.monitor_live_room()
                elif choice == "6":
                    self.search_users()
                elif choice == "7":
                    self.search_live_rooms()
                else:
                    print("无效选择，请重新输入")
                
                input("\n按回车键继续...")
                
            except KeyboardInterrupt:
                print("\n程序已退出")
                break
            except Exception as e:
                logger.error(f"程序运行错误: {e}")
                print(f"程序错误: {e}")


if __name__ == '__main__':
    interface = ConsoleInterface()
    interface.run()
