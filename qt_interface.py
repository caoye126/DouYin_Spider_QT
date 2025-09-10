#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音爬虫Qt界面
作者: 五更琉璃
日期: 2025年
"""

import sys
import os
import json
import pandas as pd
from datetime import datetime
import io
import random
import time
import requests
from contextlib import redirect_stdout, redirect_stderr
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTabWidget, QLabel, QLineEdit, 
                             QPushButton, QTextEdit, QTableWidget, QTableWidgetItem,
                             QFileDialog, QMessageBox, QProgressBar, QComboBox,
                             QGroupBox, QGridLayout, QSplitter, QFrame, QSizePolicy, QHeaderView)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPixmap, QPalette, QBrush, QIcon
from loguru import logger

# 自定义日志处理器，将日志输出重定向到GUI
class GUILogHandler:
    def __init__(self, text_widget):
        self.text_widget = text_widget
    
    def write(self, message):
        if message.strip():  # 只处理非空消息
            self.text_widget.append(message.strip())
    
    def flush(self):
        pass

# 导入原有的爬虫功能
from main import Data_Spider
from utils.common_util import init


class WorkerThread(QThread):
    """工作线程，用于执行爬虫任务"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(object)  # 改为object类型，支持dict和list
    error = pyqtSignal(str)
    
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class DataTableWidget(QTableWidget):
    """自定义表格组件，用于显示数据"""
    
    def __init__(self):
        super().__init__()
        self.setAlternatingRowColors(True)
        # 设置表格的扩展策略，确保能够充分利用空间
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # 设置表格的拉伸模式
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # 设置表格的最小高度
        self.setMinimumHeight(300)
        self.setStyleSheet("""
            QTableWidget {
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid #ddd;
                border-radius: 5px;
                gridline-color: #e0e0e0;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e0e0e0;
            }
            QTableWidget::item:selected {
                background-color: #4CAF50;
                color: white;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #4CAF50;
                font-weight: bold;
            }
        """)
    
    def load_data(self, data, data_type="json"):
        """加载数据到表格"""
        if not data:
            return
        
        if data_type == "comments":
            # 专门处理评论数据
            self.load_comments_data(data)
        elif data_type == "search_users":
            # 专门处理搜索用户数据
            self.load_search_users_data(data)
        elif data_type == "search_live":
            # 专门处理搜索直播间数据
            self.load_search_live_data(data)
        elif data_type == "user_works":
            # 专门处理用户作品数据
            self.load_user_works_data(data)
        elif data_type == "search_videos":
            # 专门处理搜索视频数据
            self.load_search_videos_data(data)
        elif data_type == "trace":
            # 专门处理留痕数据
            self.load_trace_data(data)
        elif data_type == "json" and isinstance(data, list):
            if not data:
                return
            
            # 获取所有可能的键
            all_keys = set()
            for item in data:
                if isinstance(item, dict):
                    all_keys.update(item.keys())
            
            all_keys = sorted(list(all_keys))
            
            # 设置表格
            self.setRowCount(len(data))
            self.setColumnCount(len(all_keys))
            self.setHorizontalHeaderLabels(all_keys)
            
            # 填充数据
            for row, item in enumerate(data):
                if isinstance(item, dict):
                    for col, key in enumerate(all_keys):
                        value = item.get(key, "")
                        if isinstance(value, (dict, list)):
                            value = json.dumps(value, ensure_ascii=False)
                        self.setItem(row, col, QTableWidgetItem(str(value)))
        
        elif data_type == "dict" and isinstance(data, dict):
            # 字典数据转换为键值对表格
            self.setRowCount(len(data))
            self.setColumnCount(2)
            self.setHorizontalHeaderLabels(["键", "值"])
            
            for row, (key, value) in enumerate(data.items()):
                self.setItem(row, 0, QTableWidgetItem(str(key)))
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)
                self.setItem(row, 1, QTableWidgetItem(str(value)))
        
        # 调整列宽
        self.resizeColumnsToContents()
    
    def load_comments_data(self, comments_data):
        """专门处理评论数据，转换为易读的表格格式"""
        if not comments_data or not isinstance(comments_data, list):
            return
        
        # 定义评论表格的列
        columns = [
            "评论ID", "评论内容", "用户昵称", "用户ID", "点赞数", 
            "发布时间", "用户头像", "用户主页"
        ]
        
        self.setRowCount(len(comments_data))
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
        
        for row, comment in enumerate(comments_data):
            if not isinstance(comment, dict):
                continue
            
            # 提取评论基本信息
            cid = comment.get('cid', '')
            text = comment.get('text', '')
            digg_count = comment.get('digg_count', 0)
            create_time = comment.get('create_time', 0)
            
            # 提取用户信息
            user_info = comment.get('user', {})
            nickname = user_info.get('nickname', '')
            uid = user_info.get('uid', '')
            sec_uid = user_info.get('sec_uid', '')
            
            # 处理头像URL
            avatar_url = '无'
            avatar_thumb = user_info.get('avatar_thumb', {})
            if isinstance(avatar_thumb, dict):
                url_list = avatar_thumb.get('url_list', [])
                if url_list and len(url_list) > 0:
                    avatar_url = url_list[0]
            
            # 处理时间
            time_str = '未知'
            if create_time:
                try:
                    import datetime
                    dt = datetime.datetime.fromtimestamp(create_time)
                    time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    time_str = str(create_time)
            
            # 构建用户主页链接
            user_url = f"https://www.douyin.com/user/{sec_uid}" if sec_uid else '无'
            
            # 填充表格数据
            self.setItem(row, 0, QTableWidgetItem(str(cid)))
            self.setItem(row, 1, QTableWidgetItem(str(text)))
            self.setItem(row, 2, QTableWidgetItem(str(nickname)))
            self.setItem(row, 3, QTableWidgetItem(str(uid)))
            self.setItem(row, 4, QTableWidgetItem(str(digg_count)))
            self.setItem(row, 5, QTableWidgetItem(str(time_str)))
            self.setItem(row, 6, QTableWidgetItem(str(avatar_url)))
            self.setItem(row, 7, QTableWidgetItem(str(user_url)))
    
    def load_search_users_data(self, users_data):
        """专门处理搜索用户数据，提取关键信息"""
        if not users_data or not isinstance(users_data, list):
            return
        
        # 定义要显示的列
        columns = [
            "用户ID", "用户昵称", "个性签名", "粉丝数", "关注数", 
            "获赞数", "作品数", "头像", "用户主页"
        ]
        
        self.setRowCount(len(users_data))
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
        
        for row, user in enumerate(users_data):
            if not isinstance(user, dict):
                continue
            
            # 从user_info中提取用户信息
            user_info = user.get('user_info', {})
            if not isinstance(user_info, dict):
                continue
            
            # 提取用户信息
            uid = user_info.get('uid', '')
            nickname = user_info.get('nickname', '')
            signature = user_info.get('signature', '')
            
            # 提取统计信息
            follower_count = user_info.get('follower_count', 0)
            following_count = user_info.get('following_count', 0)
            total_favorited = user_info.get('total_favorited', 0)
            aweme_count = user_info.get('aweme_count', 0)
            
            # 提取头像信息
            avatar_thumb = user_info.get('avatar_thumb', {})
            avatar_url = ''
            if isinstance(avatar_thumb, dict):
                url_list = avatar_thumb.get('url_list', [])
                if url_list:
                    avatar_url = url_list[0]
            
            # 构建用户主页链接
            sec_uid = user_info.get('sec_uid', '')
            user_url = f"https://www.douyin.com/user/{sec_uid}" if sec_uid else ''
            
            # 设置表格数据
            self.setItem(row, 0, QTableWidgetItem(str(uid)))
            self.setItem(row, 1, QTableWidgetItem(str(nickname)))
            self.setItem(row, 2, QTableWidgetItem(str(signature)))
            self.setItem(row, 3, QTableWidgetItem(str(follower_count)))
            self.setItem(row, 4, QTableWidgetItem(str(following_count)))
            self.setItem(row, 5, QTableWidgetItem(str(total_favorited)))
            self.setItem(row, 6, QTableWidgetItem(str(aweme_count)))
            self.setItem(row, 7, QTableWidgetItem(str(avatar_url)))
            self.setItem(row, 8, QTableWidgetItem(str(user_url)))
    
    def load_search_live_data(self, live_data):
        """专门处理搜索直播间数据，提取关键信息"""
        if not live_data or not isinstance(live_data, list):
            return
        
        # 定义要显示的列
        columns = [
            "直播间ID", "主播昵称", "直播间标题", "观看人数", "直播间状态",
            "主播头像", "直播间封面", "直播间链接", "主播主页"
        ]
        
        self.setRowCount(len(live_data))
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
        
        for row, live in enumerate(live_data):
            if not isinstance(live, dict):
                continue
            
            # 从lives中提取直播间信息
            lives_info = live.get('lives', {})
            if not isinstance(lives_info, dict):
                continue
            
            # 提取直播间信息
            room_id = lives_info.get('room_id', '')
            title = lives_info.get('title', '')
            user_count = lives_info.get('user_count', 0)
            status = lives_info.get('status', '')
            
            # 提取主播信息
            author = lives_info.get('author', {})
            nickname = author.get('nickname', '') if isinstance(author, dict) else ''
            sec_uid = author.get('sec_uid', '') if isinstance(author, dict) else ''
            
            # 提取头像信息
            avatar_thumb = author.get('avatar_thumb', {}) if isinstance(author, dict) else {}
            avatar_url = ''
            if isinstance(avatar_thumb, dict):
                url_list = avatar_thumb.get('url_list', [])
                if url_list:
                    avatar_url = url_list[0]
            
            # 提取直播间封面
            room_cover = author.get('room_cover', {}) if isinstance(author, dict) else {}
            cover_url = ''
            if isinstance(room_cover, dict):
                url_list = room_cover.get('url_list', [])
                if url_list:
                    cover_url = url_list[0]
            
            # 构建链接
            live_url = f"https://live.douyin.com/{room_id}" if room_id else ''
            user_url = f"https://www.douyin.com/user/{sec_uid}" if sec_uid else ''
            
            # 设置表格数据
            self.setItem(row, 0, QTableWidgetItem(str(room_id)))
            self.setItem(row, 1, QTableWidgetItem(str(nickname)))
            self.setItem(row, 2, QTableWidgetItem(str(title)))
            self.setItem(row, 3, QTableWidgetItem(str(user_count)))
            self.setItem(row, 4, QTableWidgetItem(str(status)))
            self.setItem(row, 5, QTableWidgetItem(str(avatar_url)))
            self.setItem(row, 6, QTableWidgetItem(str(cover_url)))
            self.setItem(row, 7, QTableWidgetItem(str(live_url)))
            self.setItem(row, 8, QTableWidgetItem(str(user_url)))
    
    def load_user_works_data(self, works_data):
        """专门处理用户作品数据，提取关键信息"""
        if not works_data or not isinstance(works_data, list):
            return
        
        # 定义要显示的列
        columns = [
            "作品ID", "作品标题", "作品类型", "点赞数", "评论数", "分享数", 
            "收藏数", "发布时间", "视频封面", "作品链接", "用户昵称", "用户头像"
        ]
        
        self.setRowCount(len(works_data))
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
        
        for row, work in enumerate(works_data):
            if not isinstance(work, dict):
                continue
            
            # 提取作品信息
            work_id = work.get('work_id', '')
            title = work.get('title', '')
            work_type = work.get('work_type', '')
            digg_count = work.get('digg_count', 0)
            comment_count = work.get('comment_count', 0)
            share_count = work.get('share_count', 0)
            collect_count = work.get('collect_count', 0)
            
            # 处理发布时间
            create_time = work.get('create_time', 0)
            time_str = ''
            if create_time:
                try:
                    from datetime import datetime
                    time_str = datetime.fromtimestamp(create_time).strftime('%Y-%m-%d %H:%M:%S')
                except:
                    time_str = str(create_time)
            
            # 提取视频封面
            video_cover = work.get('video_cover', '')
            
            # 构建作品链接
            work_url = work.get('work_url', '')
            
            # 提取用户信息
            nickname = work.get('nickname', '')
            author_avatar = work.get('author_avatar', '')
            
            # 设置表格数据
            self.setItem(row, 0, QTableWidgetItem(str(work_id)))
            self.setItem(row, 1, QTableWidgetItem(str(title)))
            self.setItem(row, 2, QTableWidgetItem(str(work_type)))
            self.setItem(row, 3, QTableWidgetItem(str(digg_count)))
            self.setItem(row, 4, QTableWidgetItem(str(comment_count)))
            self.setItem(row, 5, QTableWidgetItem(str(share_count)))
            self.setItem(row, 6, QTableWidgetItem(str(collect_count)))
            self.setItem(row, 7, QTableWidgetItem(str(time_str)))
            self.setItem(row, 8, QTableWidgetItem(str(video_cover)))
            self.setItem(row, 9, QTableWidgetItem(str(work_url)))
            self.setItem(row, 10, QTableWidgetItem(str(nickname)))
            self.setItem(row, 11, QTableWidgetItem(str(author_avatar)))
    
    def load_search_videos_data(self, data):
        """专门处理搜索视频数据"""
        if not isinstance(data, list) or not data:
            return
        
        # 定义要显示的列
        columns = [
            "作品ID", "标题", "作品类型", "点赞数", "评论数", "分享数", 
            "收藏数", "创建时间", "话题标签", "作者昵称", "粉丝数", "作品链接", "用户链接"
        ]
        
        # 设置表格列
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
        
        # 填充数据
        self.setRowCount(len(data))
        for row, item in enumerate(data):
            # 格式化创建时间
            create_time = item.get('create_time', '未知')
            if create_time != '未知' and create_time:
                try:
                    import datetime
                    create_time = datetime.datetime.fromtimestamp(int(create_time)).strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
            
            # 格式化粉丝数
            follower_count = item.get('follower_count', 0)
            if isinstance(follower_count, (int, float)) and follower_count > 0:
                if follower_count >= 10000:
                    follower_count = f"{follower_count/10000:.1f}万"
                else:
                    follower_count = f"{follower_count:,}"
            else:
                follower_count = "未知"
            
            row_data = [
                item.get('work_id', '未知'),
                item.get('title', '未知')[:30] + '...' if len(str(item.get('title', ''))) > 30 else item.get('title', '未知'),
                item.get('work_type', '未知'),
                f"{item.get('digg_count', 0):,}",
                f"{item.get('comment_count', 0):,}",
                f"{item.get('share_count', 0):,}",
                f"{item.get('collect_count', 0):,}",
                create_time,
                item.get('topics', '未知')[:20] + '...' if len(str(item.get('topics', ''))) > 20 else item.get('topics', '未知'),
                item.get('nickname', '未知'),
                follower_count,
                item.get('work_url', '未知'),
                item.get('user_url', '未知')
            ]
            
            for col, value in enumerate(row_data):
                self.setItem(row, col, QTableWidgetItem(str(value)))
        
        # 调整列宽
        self.resizeColumnsToContents()
        self.horizontalHeader().setStretchLastSection(True)
    
    def load_trace_data(self, data):
        """专门处理留痕数据"""
        if not isinstance(data, list) or not data:
            return
        
        # 定义要显示的列
        columns = ["用户文字", "用户链接", "访问次数"]
        
        # 设置表格列
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
        
        # 填充数据
        self.setRowCount(len(data))
        for row, item in enumerate(data):
            # 截断长文本
            text = item.get('text', '未知')
            if len(text) > 50:
                text = text[:50] + '...'
            
            row_data = [
                text,
                item.get('user_url', '未知'),
                str(item.get('visit_count', 0))
            ]
            
            for col, value in enumerate(row_data):
                self.setItem(row, col, QTableWidgetItem(str(value)))
        
        # 调整列宽
        self.resizeColumnsToContents()
        self.horizontalHeader().setStretchLastSection(True)


class DouyinSpiderGUI(QMainWindow):
    """抖音爬虫主界面"""
    
    # 定义信号
    append_text_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.data_spider = None
        self.auth = None
        
        # 连接信号槽
        self.append_text_signal.connect(self.append_live_monitor_text)
        
        self.init_ui()
        self.init_spider()
        
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("抖音爬虫工具 - 五更琉璃")
        self.setGeometry(100, 100, 1400, 900)
        
        # 设置背景
        self.set_background()
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel("🎶 抖音爬虫工具")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                background-color: rgba(255, 255, 255, 0.8);
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 10px;
            }
        """)
        main_layout.addWidget(title_label)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 5px;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #4CAF50;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #45a049;
                color: white;
            }
        """)
        
        # 创建各个功能选项卡
        self.create_tabs()
        
        main_layout.addWidget(self.tab_widget)
        
        # 状态栏
        self.statusBar().showMessage("就绪")
        
    def set_background(self):
        """设置背景图片"""
        try:
            background_path = os.path.join(os.getcwd(), 'static', 'background.jpg')
            if os.path.exists(background_path):
                # 使用样式表设置背景，避免QPainter问题
                self.setStyleSheet(f"""
                    QMainWindow {{
                        background-image: url({background_path});
                        background-repeat: no-repeat;
                        background-position: center;
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                            stop:0 rgba(102, 126, 234, 0.8), stop:1 rgba(118, 75, 162, 0.8));
                    }}
                """)
            else:
                # 如果没有背景图，设置渐变背景
                self.setStyleSheet("""
                    QMainWindow {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                            stop:0 #667eea, stop:1 #764ba2);
                    }
                """)
        except Exception as e:
            # 如果背景设置失败，使用简单的渐变背景
            self.setStyleSheet("""
                QMainWindow {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #667eea, stop:1 #764ba2);
                }
            """)
            logger.warning(f"背景设置失败，使用默认背景: {e}")
    
    def create_tabs(self):
        """创建功能选项卡"""
        # 1. 爬取单个视频信息
        self.create_single_video_tab()
        
        # 2. 爬取用户所有作品
        self.create_user_works_tab()
        
        # 3. 搜索视频
        self.create_search_videos_tab()
        
        # 4. 爬取视频评论区
        self.create_comments_tab()
        
        # 5. 监听直播间
        self.create_live_monitor_tab()
        
        # 6. 搜索用户
        self.create_search_users_tab()
        
        # 7. 搜索直播间
        self.create_search_live_tab()
        
        # 8. 关键词筛选
        self.create_keyword_filter_tab()
        
        # 9. 留痕功能
        self.create_trace_function_tab()
    
    def create_single_video_tab(self):
        """创建单个视频爬取选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 输入区域
        input_group = QGroupBox("视频信息输入")
        input_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #4CAF50;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        input_layout = QGridLayout(input_group)
        
        input_layout.addWidget(QLabel("视频URL:"), 0, 0)
        self.single_video_url = QLineEdit()
        self.single_video_url.setPlaceholderText("请输入抖音视频链接")
        input_layout.addWidget(self.single_video_url, 0, 1)
        
        self.single_video_btn = QPushButton("开始爬取")
        self.single_video_btn.setStyleSheet(self.get_button_style())
        self.single_video_btn.clicked.connect(self.crawl_single_video)
        input_layout.addWidget(self.single_video_btn, 0, 2)
        
        layout.addWidget(input_group)
        
        # 结果显示区域
        result_group = QGroupBox("爬取结果")
        result_group.setStyleSheet(input_group.styleSheet())
        result_layout = QVBoxLayout(result_group)
        
        # 数据表格
        self.single_video_table = DataTableWidget()
        result_layout.addWidget(self.single_video_table)
        
        layout.addWidget(result_group)
        
        # 进度显示区域
        progress_group = QGroupBox("爬取进度")
        progress_group.setStyleSheet(self.get_group_style())
        progress_layout = QVBoxLayout(progress_group)
        
        self.single_video_progress = QTextEdit()
        self.single_video_progress.setMaximumHeight(100)
        self.single_video_progress.setReadOnly(True)
        self.single_video_progress.setPlaceholderText("爬取进度将在此显示...")
        progress_layout.addWidget(self.single_video_progress)
        
        layout.addWidget(progress_group)
        
        # 保存按钮
        save_layout = QHBoxLayout()
        self.single_video_save_btn = QPushButton("复制数据到其他位置")
        self.single_video_save_btn.setStyleSheet(self.get_button_style())
        self.single_video_save_btn.clicked.connect(lambda: self.save_data("single_video"))
        save_layout.addWidget(self.single_video_save_btn)
        save_layout.addStretch()
        layout.addLayout(save_layout)
        
        self.tab_widget.addTab(tab, "单个视频")
        self.single_video_data = None
    
    def create_user_works_tab(self):
        """创建用户作品爬取选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 输入区域
        input_group = QGroupBox("用户信息输入")
        input_group.setStyleSheet(self.get_group_style())
        input_layout = QGridLayout(input_group)
        
        input_layout.addWidget(QLabel("用户URL:"), 0, 0)
        self.user_works_url = QLineEdit()
        self.user_works_url.setPlaceholderText("请输入抖音用户链接")
        input_layout.addWidget(self.user_works_url, 0, 1)
        
        self.user_works_btn = QPushButton("开始爬取")
        self.user_works_btn.setStyleSheet(self.get_button_style())
        self.user_works_btn.clicked.connect(self.crawl_user_works)
        input_layout.addWidget(self.user_works_btn, 0, 2)
        
        layout.addWidget(input_group)
        
        # 结果显示区域（上面）
        result_group = QGroupBox("爬取结果")
        result_group.setStyleSheet(self.get_group_style())
        result_layout = QVBoxLayout(result_group)
        
        self.user_works_table = DataTableWidget()
        # 设置表格的扩展策略，确保能够充分利用空间
        self.user_works_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # 设置表格的最小高度，确保有足够的显示空间
        self.user_works_table.setMinimumHeight(400)
        result_layout.addWidget(self.user_works_table)
        
        layout.addWidget(result_group)
        
        # 进度显示区域（下面）
        progress_group = QGroupBox("爬取进度")
        progress_group.setStyleSheet(self.get_group_style())
        progress_layout = QVBoxLayout(progress_group)
        
        self.user_works_progress = QTextEdit()
        # 设置进度区域的扩展策略，充分利用空间
        self.user_works_progress.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # 设置最小高度，确保有足够的显示空间
        self.user_works_progress.setMinimumHeight(200)
        self.user_works_progress.setReadOnly(True)
        self.user_works_progress.setPlaceholderText("爬取进度将在此显示...")
        progress_layout.addWidget(self.user_works_progress)
        
        layout.addWidget(progress_group)
        
        save_layout = QHBoxLayout()
        self.user_works_save_btn = QPushButton("复制数据到其他位置")
        self.user_works_save_btn.setStyleSheet(self.get_button_style())
        self.user_works_save_btn.clicked.connect(lambda: self.save_data("user_works"))
        save_layout.addWidget(self.user_works_save_btn)
        save_layout.addStretch()
        result_layout.addLayout(save_layout)
        
        self.tab_widget.addTab(tab, "用户作品")
        self.user_works_data = None
    
    def create_search_videos_tab(self):
        """创建搜索视频选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 输入区域
        input_group = QGroupBox("搜索条件")
        input_group.setStyleSheet(self.get_group_style())
        input_layout = QGridLayout(input_group)
        
        input_layout.addWidget(QLabel("搜索关键词:"), 0, 0)
        self.search_videos_keyword = QLineEdit()
        self.search_videos_keyword.setPlaceholderText("请输入搜索关键词")
        input_layout.addWidget(self.search_videos_keyword, 0, 1)
        
        input_layout.addWidget(QLabel("数量:"), 1, 0)
        self.search_videos_count = QLineEdit()
        self.search_videos_count.setPlaceholderText("请输入要获取的视频数量")
        self.search_videos_count.setText("20")
        input_layout.addWidget(self.search_videos_count, 1, 1)
        
        self.search_videos_btn = QPushButton("开始搜索")
        self.search_videos_btn.setStyleSheet(self.get_button_style())
        self.search_videos_btn.clicked.connect(self.search_videos)
        input_layout.addWidget(self.search_videos_btn, 1, 2)
        
        layout.addWidget(input_group)
        
        # 结果显示区域（上面）
        result_group = QGroupBox("搜索结果")
        result_group.setStyleSheet(self.get_group_style())
        result_layout = QVBoxLayout(result_group)
        
        self.search_videos_table = DataTableWidget()
        # 设置表格的扩展策略，确保能够充分利用空间
        self.search_videos_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # 设置表格的最小高度，确保有足够的显示空间
        self.search_videos_table.setMinimumHeight(400)
        result_layout.addWidget(self.search_videos_table)
        
        save_layout = QHBoxLayout()
        self.search_videos_save_btn = QPushButton("复制数据到其他位置")
        self.search_videos_save_btn.setStyleSheet(self.get_button_style())
        self.search_videos_save_btn.clicked.connect(lambda: self.save_data("search_videos"))
        save_layout.addWidget(self.search_videos_save_btn)
        save_layout.addStretch()
        result_layout.addLayout(save_layout)
        
        layout.addWidget(result_group)
        
        # 进度显示区域（下面）
        progress_group = QGroupBox("搜索进度")
        progress_group.setStyleSheet(self.get_group_style())
        progress_layout = QVBoxLayout(progress_group)
        
        self.search_videos_progress = QTextEdit()
        # 设置进度区域的扩展策略，充分利用空间
        self.search_videos_progress.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # 设置最小高度，确保有足够的显示空间
        self.search_videos_progress.setMinimumHeight(150)
        self.search_videos_progress.setReadOnly(True)
        self.search_videos_progress.setPlaceholderText("搜索进度将在此显示...")
        progress_layout.addWidget(self.search_videos_progress)
        
        layout.addWidget(progress_group)
        
        self.tab_widget.addTab(tab, "搜索视频")
        self.search_videos_data = None
    
    def create_comments_tab(self):
        """创建视频评论爬取选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 输入区域
        input_group = QGroupBox("视频信息输入")
        input_group.setStyleSheet(self.get_group_style())
        input_layout = QGridLayout(input_group)
        
        input_layout.addWidget(QLabel("视频URL:"), 0, 0)
        self.comments_url = QLineEdit()
        self.comments_url.setPlaceholderText("请输入抖音视频链接")
        input_layout.addWidget(self.comments_url, 0, 1)
        
        self.comments_btn = QPushButton("开始爬取评论")
        self.comments_btn.setStyleSheet(self.get_button_style())
        self.comments_btn.clicked.connect(self.crawl_comments)
        input_layout.addWidget(self.comments_btn, 0, 2)
        
        layout.addWidget(input_group)
        
        # 结果显示区域（上面）
        result_group = QGroupBox("评论结果")
        result_group.setStyleSheet(self.get_group_style())
        result_layout = QVBoxLayout(result_group)
        
        self.comments_table = DataTableWidget()
        # 设置表格的扩展策略，确保能够充分利用空间
        self.comments_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # 设置表格的最小高度，确保有足够的显示空间
        self.comments_table.setMinimumHeight(400)
        result_layout.addWidget(self.comments_table)
        
        layout.addWidget(result_group)
        
        # 进度显示区域（下面）
        progress_group = QGroupBox("爬取进度")
        progress_group.setStyleSheet(self.get_group_style())
        progress_layout = QVBoxLayout(progress_group)
        
        self.comments_progress = QTextEdit()
        # 设置进度区域的扩展策略，充分利用空间
        self.comments_progress.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # 设置最小高度，确保有足够的显示空间
        self.comments_progress.setMinimumHeight(150)
        self.comments_progress.setReadOnly(True)
        self.comments_progress.setPlaceholderText("爬取进度将在此显示...")
        progress_layout.addWidget(self.comments_progress)
        
        layout.addWidget(progress_group)
        
        save_layout = QHBoxLayout()
        self.comments_save_btn = QPushButton("复制数据到其他位置")
        self.comments_save_btn.setStyleSheet(self.get_button_style())
        self.comments_save_btn.clicked.connect(lambda: self.save_data("comments"))
        save_layout.addWidget(self.comments_save_btn)
        save_layout.addStretch()
        result_layout.addLayout(save_layout)
        
        layout.addWidget(result_group)
        
        self.tab_widget.addTab(tab, "视频评论")
        self.comments_data = None
    
    def create_live_monitor_tab(self):
        """创建直播间监听选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 输入区域
        input_group = QGroupBox("直播间信息")
        input_group.setStyleSheet(self.get_group_style())
        input_layout = QGridLayout(input_group)
        
        input_layout.addWidget(QLabel("直播间ID:"), 0, 0)
        self.live_monitor_id = QLineEdit()
        self.live_monitor_id.setPlaceholderText("请输入直播间ID")
        input_layout.addWidget(self.live_monitor_id, 0, 1)
        
        self.live_monitor_btn = QPushButton("开始监听")
        self.live_monitor_btn.setStyleSheet(self.get_button_style())
        self.live_monitor_btn.clicked.connect(self.monitor_live)
        input_layout.addWidget(self.live_monitor_btn, 0, 2)
        
        self.live_monitor_stop_btn = QPushButton("停止监听")
        self.live_monitor_stop_btn.setStyleSheet(self.get_button_style())
        self.live_monitor_stop_btn.clicked.connect(self.stop_live_monitor)
        self.live_monitor_stop_btn.setEnabled(False)
        input_layout.addWidget(self.live_monitor_stop_btn, 0, 3)
        
        layout.addWidget(input_group)
        
        # 结果显示区域
        result_group = QGroupBox("监听结果")
        result_group.setStyleSheet(self.get_group_style())
        result_layout = QVBoxLayout(result_group)
        
        self.live_monitor_text = QTextEdit()
        self.live_monitor_text.setStyleSheet("""
            QTextEdit {
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid #ddd;
                border-radius: 5px;
                font-family: 'Consolas', 'Monaco', monospace;
            }
        """)
        result_layout.addWidget(self.live_monitor_text)
        
        # 保存按钮
        save_layout = QHBoxLayout()
        self.live_monitor_save_btn = QPushButton("保存监听数据")
        self.live_monitor_save_btn.setStyleSheet(self.get_button_style())
        self.live_monitor_save_btn.clicked.connect(self.save_live_monitor_data)
        save_layout.addWidget(self.live_monitor_save_btn)
        save_layout.addStretch()
        result_layout.addLayout(save_layout)
        
        layout.addWidget(result_group)
        
        self.tab_widget.addTab(tab, "直播间监听")
        self.live_monitor_data = []
        self.live_monitor_ws = None
    
    def create_search_users_tab(self):
        """创建搜索用户选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 输入区域
        input_group = QGroupBox("搜索条件")
        input_group.setStyleSheet(self.get_group_style())
        input_layout = QGridLayout(input_group)
        
        input_layout.addWidget(QLabel("搜索关键词:"), 0, 0)
        self.search_users_keyword = QLineEdit()
        self.search_users_keyword.setPlaceholderText("请输入搜索关键词")
        input_layout.addWidget(self.search_users_keyword, 0, 1)
        
        input_layout.addWidget(QLabel("数量:"), 1, 0)
        self.search_users_count = QLineEdit()
        self.search_users_count.setPlaceholderText("请输入要获取的用户数量")
        self.search_users_count.setText("20")
        input_layout.addWidget(self.search_users_count, 1, 1)
        
        self.search_users_btn = QPushButton("开始搜索")
        self.search_users_btn.setStyleSheet(self.get_button_style())
        self.search_users_btn.clicked.connect(self.search_users)
        input_layout.addWidget(self.search_users_btn, 1, 2)
        
        layout.addWidget(input_group)
        
        # 结果显示区域
        result_group = QGroupBox("搜索结果")
        result_group.setStyleSheet(self.get_group_style())
        result_layout = QVBoxLayout(result_group)
        
        self.search_users_table = DataTableWidget()
        result_layout.addWidget(self.search_users_table)
        
        save_layout = QHBoxLayout()
        self.search_users_save_btn = QPushButton("复制数据到其他位置")
        self.search_users_save_btn.setStyleSheet(self.get_button_style())
        self.search_users_save_btn.clicked.connect(lambda: self.save_data("search_users"))
        save_layout.addWidget(self.search_users_save_btn)
        save_layout.addStretch()
        result_layout.addLayout(save_layout)
        
        layout.addWidget(result_group)
        
        self.tab_widget.addTab(tab, "搜索用户")
        self.search_users_data = None
    
    def create_search_live_tab(self):
        """创建搜索直播间选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 输入区域
        input_group = QGroupBox("搜索条件")
        input_group.setStyleSheet(self.get_group_style())
        input_layout = QGridLayout(input_group)
        
        input_layout.addWidget(QLabel("搜索关键词:"), 0, 0)
        self.search_live_keyword = QLineEdit()
        self.search_live_keyword.setPlaceholderText("请输入搜索关键词")
        input_layout.addWidget(self.search_live_keyword, 0, 1)
        
        input_layout.addWidget(QLabel("数量:"), 1, 0)
        self.search_live_count = QLineEdit()
        self.search_live_count.setPlaceholderText("请输入要获取的直播间数量")
        self.search_live_count.setText("20")
        input_layout.addWidget(self.search_live_count, 1, 1)
        
        self.search_live_btn = QPushButton("开始搜索")
        self.search_live_btn.setStyleSheet(self.get_button_style())
        self.search_live_btn.clicked.connect(self.search_live_rooms)
        input_layout.addWidget(self.search_live_btn, 1, 2)
        
        layout.addWidget(input_group)
        
        # 结果显示区域
        result_group = QGroupBox("搜索结果")
        result_group.setStyleSheet(self.get_group_style())
        result_layout = QVBoxLayout(result_group)
        
        self.search_live_table = DataTableWidget()
        result_layout.addWidget(self.search_live_table)
        
        save_layout = QHBoxLayout()
        self.search_live_save_btn = QPushButton("复制数据到其他位置")
        self.search_live_save_btn.setStyleSheet(self.get_button_style())
        self.search_live_save_btn.clicked.connect(lambda: self.save_data("search_live"))
        save_layout.addWidget(self.search_live_save_btn)
        save_layout.addStretch()
        result_layout.addLayout(save_layout)
        
        layout.addWidget(result_group)
        
        self.tab_widget.addTab(tab, "搜索直播间")
        self.search_live_data = None
    
    def create_keyword_filter_tab(self):
        """创建关键词筛选标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 输入区域
        input_group = QGroupBox("关键词筛选设置")
        input_group.setStyleSheet(self.get_group_style())
        input_layout = QGridLayout(input_group)
        
        # 关键词输入
        input_layout.addWidget(QLabel("关键词:"), 0, 0)
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("请输入要筛选的关键词")
        input_layout.addWidget(self.keyword_input, 0, 1)
        
        # 数据类型选择
        input_layout.addWidget(QLabel("数据类型:"), 1, 0)
        self.data_type_combo = QComboBox()
        self.data_type_combo.addItems(["评论数据", "直播监听数据"])
        input_layout.addWidget(self.data_type_combo, 1, 1)
        
        # 筛选按钮
        self.filter_btn = QPushButton("开始筛选")
        self.filter_btn.setStyleSheet(self.get_button_style())
        self.filter_btn.clicked.connect(self.filter_keywords)
        input_layout.addWidget(self.filter_btn, 2, 0, 1, 2)
        
        layout.addWidget(input_group)
        
        # 结果展示区域
        result_group = QGroupBox("筛选结果")
        result_group.setStyleSheet(self.get_group_style())
        result_layout = QVBoxLayout(result_group)
        
        # 结果表格
        self.filter_table = QTableWidget()
        self.filter_table.setColumnCount(2)
        self.filter_table.setHorizontalHeaderLabels(["用户文字", "用户链接"])
        self.filter_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.filter_table.setMinimumHeight(400)
        self.filter_table.horizontalHeader().setStretchLastSection(True)
        result_layout.addWidget(self.filter_table)
        
        # 保存按钮
        save_layout = QHBoxLayout()
        self.save_filter_btn = QPushButton("保存结果")
        self.save_filter_btn.setStyleSheet(self.get_button_style())
        self.save_filter_btn.clicked.connect(self.save_filter_results)
        save_layout.addWidget(self.save_filter_btn)
        save_layout.addStretch()
        result_layout.addLayout(save_layout)
        
        layout.addWidget(result_group)
        
        # 进度显示区域
        progress_group = QGroupBox("筛选进度")
        progress_group.setStyleSheet(self.get_group_style())
        progress_layout = QVBoxLayout(progress_group)
        
        self.filter_progress = QTextEdit()
        self.filter_progress.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.filter_progress.setMinimumHeight(150)
        self.filter_progress.setReadOnly(True)
        progress_layout.addWidget(self.filter_progress)
        
        layout.addWidget(progress_group)
        
        self.tab_widget.addTab(tab, "关键词筛选")
        self.filter_data = []
        
        return tab
    
    def create_trace_function_tab(self):
        """创建留痕功能标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 输入区域
        input_group = QGroupBox("留痕功能设置")
        input_group.setStyleSheet(self.get_group_style())
        input_layout = QGridLayout(input_group)
        
        # 访问次数设置
        input_layout.addWidget(QLabel("访问次数:"), 0, 0)
        self.visit_count_input = QLineEdit()
        self.visit_count_input.setPlaceholderText("请输入访问次数(2-5次)")
        self.visit_count_input.setText("3")
        input_layout.addWidget(self.visit_count_input, 0, 1)
        
        # 开始留痕按钮
        self.trace_btn = QPushButton("开始留痕")
        self.trace_btn.setStyleSheet(self.get_button_style())
        self.trace_btn.clicked.connect(self.start_trace_function)
        input_layout.addWidget(self.trace_btn, 0, 2)
        
        layout.addWidget(input_group)
        
        # 结果展示区域
        result_group = QGroupBox("留痕结果")
        result_group.setStyleSheet(self.get_group_style())
        result_layout = QVBoxLayout(result_group)
        
        # 结果表格
        self.trace_table = DataTableWidget()
        self.trace_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.trace_table.setMinimumHeight(400)
        result_layout.addWidget(self.trace_table)
        
        # 保存按钮
        save_layout = QHBoxLayout()
        self.save_trace_btn = QPushButton("保存结果")
        self.save_trace_btn.setStyleSheet(self.get_button_style())
        self.save_trace_btn.clicked.connect(lambda: self.save_data("trace", self.trace_data))
        save_layout.addWidget(self.save_trace_btn)
        save_layout.addStretch()
        result_layout.addLayout(save_layout)
        
        layout.addWidget(result_group)
        
        # 进度显示区域
        progress_group = QGroupBox("留痕进度")
        progress_group.setStyleSheet(self.get_group_style())
        progress_layout = QVBoxLayout(progress_group)
        
        self.trace_progress = QTextEdit()
        self.trace_progress.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.trace_progress.setMinimumHeight(150)
        self.trace_progress.setReadOnly(True)
        progress_layout.addWidget(self.trace_progress)
        
        layout.addWidget(progress_group)
        
        self.tab_widget.addTab(tab, "留痕功能")
        self.trace_data = []
        
        return tab
    
    def get_button_style(self):
        """获取按钮样式"""
        return """
            QPushButton {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 10px 20px;
                text-align: center;
                font-size: 14px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """
    
    def get_group_style(self):
        """获取分组框样式"""
        return """
            QGroupBox {
                font-weight: bold;
                border: 2px solid #4CAF50;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """
    
    def init_spider(self):
        """初始化爬虫"""
        try:
            # 初始化数据目录
            init()
            
            # 创建爬虫实例
            self.data_spider = Data_Spider()
            self.auth = self.data_spider.auth
            
            self.statusBar().showMessage("爬虫初始化成功")
            logger.info("爬虫初始化成功")
        except Exception as e:
            QMessageBox.critical(self, "初始化错误", f"爬虫初始化失败: {str(e)}")
            logger.error(f"爬虫初始化失败: {e}")
    
    def crawl_single_video(self):
        """爬取单个视频"""
        url = self.single_video_url.text().strip()
        if not url:
            QMessageBox.warning(self, "输入错误", "请输入视频URL")
            return
        
        # 显示进度信息
        self.single_video_progress.append(f"开始爬取视频: {url}")
        
        self.single_video_btn.setEnabled(False)
        self.single_video_btn.setText("爬取中...")
        
        # 创建工作线程
        self.worker = WorkerThread(self.data_spider.spider_work_simple, url)
        self.worker.finished.connect(self.on_single_video_finished)
        self.worker.error.connect(self.on_worker_error)
        self.worker.start()
    
    def on_single_video_finished(self, result):
        """单个视频爬取完成"""
        self.single_video_data = result
        self.single_video_table.load_data([result], "dict")
        
        # 显示进度信息
        self.single_video_progress.append(f"视频爬取完成: {result.get('title', 'Unknown')}")
        
        # 自动保存到默认位置
        self.auto_save_data("single_video", result)
        
        self.single_video_btn.setEnabled(True)
        self.single_video_btn.setText("开始爬取")
        self.statusBar().showMessage("单个视频爬取完成")
    
    def crawl_user_works(self):
        """爬取用户作品"""
        url = self.user_works_url.text().strip()
        if not url:
            QMessageBox.warning(self, "输入错误", "请输入用户URL")
            return
        
        # 清空进度显示
        self.user_works_progress.clear()
        
        # 显示进度信息
        self.user_works_progress.append(f"开始爬取用户作品: {url}")
        self.user_works_progress.append("正在解析用户信息...")
        
        self.user_works_btn.setEnabled(False)
        self.user_works_btn.setText("爬取中...")
        
        # 创建工作线程
        self.worker = WorkerThread(self.data_spider.spider_user_all_work_simple, url)
        self.worker.finished.connect(self.on_user_works_finished)
        self.worker.error.connect(self.on_worker_error)
        self.worker.start()
    
    def on_user_works_finished(self, result):
        """用户作品爬取完成"""
        self.user_works_data = result
        if isinstance(result, list):
            self.user_works_table.load_data(result, "user_works")
            self.user_works_progress.append(f"✅ 用户作品爬取完成，共获取 {len(result)} 个作品")
            
            # 显示作品统计信息
            if result:
                first_work = result[0]
                nickname = first_work.get('nickname', '未知用户')
                self.user_works_progress.append(f"📊 用户: {nickname}")
                
                # 统计作品类型
                video_count = sum(1 for work in result if work.get('work_type') == '视频')
                image_count = len(result) - video_count
                self.user_works_progress.append(f"📹 视频作品: {video_count} 个")
                self.user_works_progress.append(f"🖼️ 图片作品: {image_count} 个")
                
                # 统计互动数据
                total_likes = sum(work.get('digg_count', 0) for work in result)
                total_comments = sum(work.get('comment_count', 0) for work in result)
                total_shares = sum(work.get('share_count', 0) for work in result)
                self.user_works_progress.append(f"👍 总点赞数: {total_likes:,}")
                self.user_works_progress.append(f"💬 总评论数: {total_comments:,}")
                self.user_works_progress.append(f"📤 总分享数: {total_shares:,}")
        else:
            self.user_works_table.load_data([result], "dict")
            self.user_works_progress.append("✅ 用户作品爬取完成")
        
        # 自动保存到默认位置
        self.auto_save_data("user_works", result)
        
        self.user_works_btn.setEnabled(True)
        self.user_works_btn.setText("开始爬取")
        self.statusBar().showMessage("用户作品爬取完成")
    
    def search_videos(self):
        """搜索视频"""
        keyword = self.search_videos_keyword.text().strip()
        count = self.search_videos_count.text().strip()
        
        if not keyword:
            QMessageBox.warning(self, "输入错误", "请输入搜索关键词")
            return
        
        try:
            count = int(count) if count else 20
        except ValueError:
            QMessageBox.warning(self, "输入错误", "请输入有效的数量")
            return
        
        self.search_videos_btn.setEnabled(False)
        self.search_videos_btn.setText("搜索中...")
        
        # 显示进度信息
        self.search_videos_progress.clear()
        self.search_videos_progress.append(f"🔍 开始搜索视频: {keyword}")
        self.search_videos_progress.append(f"📊 搜索数量: {count}")
        self.search_videos_progress.append("⏳ 正在连接服务器...")
        
        # 创建工作线程
        self.worker = WorkerThread(self.data_spider.spider_search_videos_simple, 
                                 keyword, count)
        self.worker.finished.connect(self.on_search_videos_finished)
        self.worker.error.connect(self.on_worker_error)
        self.worker.start()
    
    def on_search_videos_finished(self, result):
        """视频搜索完成"""
        self.search_videos_data = result
        self.search_videos_table.load_data(result, "search_videos")
        
        # 显示详细的搜索结果统计
        if isinstance(result, list) and result:
            self.search_videos_progress.append(f"✅ 视频搜索完成，共找到 {len(result)} 个结果")
            
            # 统计视频类型
            video_count = sum(1 for item in result if item.get('work_type') == '视频')
            image_count = len(result) - video_count
            self.search_videos_progress.append(f"📹 视频作品: {video_count} 个")
            self.search_videos_progress.append(f"🖼️ 图片作品: {image_count} 个")
            
            # 统计互动数据
            total_likes = sum(item.get('digg_count', 0) for item in result)
            total_comments = sum(item.get('comment_count', 0) for item in result)
            total_shares = sum(item.get('share_count', 0) for item in result)
            self.search_videos_progress.append(f"👍 总点赞数: {total_likes:,}")
            self.search_videos_progress.append(f"💬 总评论数: {total_comments:,}")
            self.search_videos_progress.append(f"📤 总分享数: {total_shares:,}")
        else:
            self.search_videos_progress.append("⚠️ 未找到相关视频")
        
        # 自动保存到默认位置
        self.auto_save_data("search_videos", result)
        
        self.search_videos_btn.setEnabled(True)
        self.search_videos_btn.setText("开始搜索")
        self.statusBar().showMessage(f"视频搜索完成，找到 {len(result) if isinstance(result, list) else 0} 个结果")
    
    def crawl_comments(self):
        """爬取视频评论"""
        url = self.comments_url.text().strip()
        if not url:
            QMessageBox.warning(self, "输入错误", "请输入视频URL")
            return
        
        # 显示进度信息
        self.comments_progress.append(f"开始解析URL: {url}")
        
        # 解析URL获取视频ID
        try:
            import re
            from urllib.parse import urlparse, parse_qs
            
            # 尝试从URL中提取视频ID
            video_id = None
            
            # 方法1: 从modal_id参数中提取
            if 'modal_id=' in url:
                match = re.search(r'modal_id=(\d+)', url)
                if match:
                    video_id = match.group(1)
                    self.comments_progress.append(f"从modal_id参数提取到视频ID: {video_id}")
            
            # 方法2: 从标准视频URL中提取
            if not video_id:
                match = re.search(r'/video/(\d+)', url)
                if match:
                    video_id = match.group(1)
                    self.comments_progress.append(f"从视频URL提取到视频ID: {video_id}")
            
            if not video_id:
                raise ValueError("无法从URL中提取视频ID")
            
            # 构建标准的视频URL
            standard_url = f"https://www.douyin.com/video/{video_id}"
            self.comments_progress.append(f"使用标准URL: {standard_url}")
            self.comments_progress.append(f"视频ID长度: {len(video_id)} 位")
            
        except Exception as e:
            self.comments_progress.append(f"URL解析失败: {str(e)}")
            QMessageBox.warning(self, "URL解析错误", f"无法解析视频URL: {str(e)}")
            return
        
        self.comments_btn.setEnabled(False)
        self.comments_btn.setText("爬取中...")
        self.comments_progress.append("开始爬取评论...")
        self.comments_progress.append("正在连接服务器...")
        
        # 创建工作线程
        self.worker = WorkerThread(self.data_spider.spider_work_comments, standard_url)
        self.worker.finished.connect(self.on_comments_finished)
        self.worker.error.connect(self.on_worker_error)
        self.worker.start()
    
    def on_comments_finished(self, result):
        """评论爬取完成"""
        self.comments_data = result
        if isinstance(result, list):
            self.comments_table.load_data(result, "comments")
            self.comments_progress.append(f"✅ 评论爬取完成，共获取 {len(result)} 条评论")
            
            # 统计评论信息
            if result:
                # 统计回复评论数量
                reply_count = sum(comment.get('reply_comment_total', 0) for comment in result)
                self.comments_progress.append(f"💬 一级评论: {len(result)} 条")
                self.comments_progress.append(f"🔄 回复评论: {reply_count} 条")
                
                # 统计点赞数
                total_likes = sum(comment.get('digg_count', 0) for comment in result)
                self.comments_progress.append(f"👍 总点赞数: {total_likes:,}")
                
                # 显示热门评论
                if len(result) > 0:
                    top_comment = max(result, key=lambda x: x.get('digg_count', 0))
                    self.comments_progress.append(f"🔥 热门评论: {top_comment.get('text', '')[:30]}...")
        else:
            self.comments_table.load_data([result], "dict")
            self.comments_progress.append("✅ 评论爬取完成")
        
        # 自动保存到默认位置
        self.auto_save_data("comments", result)
        
        self.comments_btn.setEnabled(True)
        self.comments_btn.setText("开始爬取评论")
        self.statusBar().showMessage("评论爬取完成")
    
    def monitor_live(self):
        """监听直播间"""
        live_id = self.live_monitor_id.text().strip()
        if not live_id:
            QMessageBox.warning(self, "输入错误", "请输入直播间ID")
            return
        
        # 显示进度信息
        self.live_monitor_text.append(f"开始监听直播间: {live_id}")
        self.live_monitor_text.append("正在获取直播间信息...")
        
        self.live_monitor_btn.setEnabled(False)
        self.live_monitor_btn.setText("监听中...")
        self.live_monitor_stop_btn.setEnabled(True)
        
        # 创建工作线程进行直播间监听
        self.worker = WorkerThread(self.start_live_monitoring, live_id)
        self.worker.finished.connect(self.on_live_monitor_finished)
        self.worker.error.connect(self.on_worker_error)
        self.worker.start()
    
    def start_live_monitoring(self, live_id):
        """启动直播间监听"""
        try:
            # 检查直播间状态
            live_info = self.data_spider.douyin_apis.get_live_info(self.auth, live_id)
            if live_info:
                room_title = live_info.get('room_title', 'N/A')
                room_status = live_info.get('room_status', '0')
                
                # 发送直播间信息到UI
                self.live_monitor_text.append(f"直播间标题: {room_title}")
                self.live_monitor_text.append(f"直播间状态: {'直播中' if room_status == '2' else '未开播'}")
                
                if room_status == '2':
                    self.live_monitor_text.append("开始监听直播间弹幕和礼物...")
                    
                    # 启动WebSocket监听
                    from dy_live.server import DouyinLive
                    live_monitor = DouyinLive(live_id, self.auth)
                    self.live_monitor_ws = live_monitor  # 保存WebSocket实例
                    
                    # 重写消息处理方法以适配Qt界面
                    def qt_on_message(ws, message):
                        try:
                            import gzip
                            import static.Live_pb2 as Live_pb2
                            from datetime import datetime
                            
                            frame = Live_pb2.PushFrame()
                            frame.ParseFromString(message)
                            origin_bytes = gzip.decompress(frame.payload)
                            response = Live_pb2.LiveResponse()
                            response.ParseFromString(origin_bytes)
                            
                            if response.needAck:
                                s = Live_pb2.PushFrame()
                                s.payloadType = "ack"
                                s.payload = response.internalExt.encode('utf-8')
                                s.logId = frame.logId
                                ws.send(s.SerializeToString(), opcode=0x02)
                            
                            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            
                            for item in response.messagesList:
                                if item.method == 'WebcastGiftMessage':
                                    message = Live_pb2.GiftMessage()
                                    message.ParseFromString(item.payload)
                                    gift_info = f"[礼物] {message.user.nickname} 送给 {message.toUser.nickname} {message.gift.name} x {message.comboCount}"
                                    # 使用信号发送到主线程更新UI
                                    self.append_text_signal.emit(gift_info)
                                    
                                    # 保存礼物数据
                                    gift_data = {
                                        'type': 'gift',
                                        'time': current_time,
                                        'user_nickname': message.user.nickname,
                                        'user_sec_uid': message.user.sec_uid,
                                        'to_user_nickname': message.toUser.nickname,
                                        'to_user_sec_uid': message.toUser.sec_uid,
                                        'gift_name': message.gift.name,
                                        'gift_count': message.comboCount,
                                        'gift_value': getattr(message.gift, 'diamondCount', 0)
                                    }
                                    self.live_monitor_data.append(gift_data)
                                    
                                elif item.method == "WebcastChatMessage":
                                    message = Live_pb2.ChatMessage()
                                    message.ParseFromString(item.payload)
                                    chat_info = f"[弹幕] {message.user.nickname}: {message.content}"
                                    self.append_text_signal.emit(chat_info)
                                    
                                    # 保存弹幕数据
                                    chat_data = {
                                        'type': 'chat',
                                        'time': current_time,
                                        'user_nickname': message.user.nickname,
                                        'user_sec_uid': message.user.sec_uid,
                                        'content': message.content,
                                        'user_level': getattr(message.user, 'user_level', 0)
                                    }
                                    self.live_monitor_data.append(chat_data)
                                    
                                elif item.method == "WebcastMemberMessage":
                                    message = Live_pb2.MemberMessage()
                                    message.ParseFromString(item.payload)
                                    member_info = f"[进入] {message.user.nickname} 进入直播间"
                                    self.append_text_signal.emit(member_info)
                                    
                                    # 保存进入数据
                                    member_data = {
                                        'type': 'member',
                                        'time': current_time,
                                        'user_nickname': message.user.nickname,
                                        'user_sec_uid': message.user.sec_uid
                                    }
                                    self.live_monitor_data.append(member_data)
                                    
                                elif item.method == "WebcastLikeMessage":
                                    message = Live_pb2.LikeMessage()
                                    message.ParseFromString(item.payload)
                                    like_info = f"[点赞] {message.user.nickname} 点赞了"
                                    self.append_text_signal.emit(like_info)
                                    
                                    # 保存点赞数据
                                    like_data = {
                                        'type': 'like',
                                        'time': current_time,
                                        'user_nickname': message.user.nickname,
                                        'user_sec_uid': message.user.sec_uid,
                                        'like_count': getattr(message, 'count', 1)
                                    }
                                    self.live_monitor_data.append(like_data)
                                    
                        except Exception as e:
                            self.append_text_signal.emit(f"处理消息时出错: {str(e)}")
                    
                    # 重写on_open方法
                    def qt_on_open(ws):
                        self.append_text_signal.emit("WebSocket连接已建立")
                        # 启动ping线程
                        import threading
                        import time
                        
                        def ping():
                            while True:
                                try:
                                    import static.Live_pb2 as Live_pb2
                                    frame = Live_pb2.PushFrame()
                                    frame.payloadType = "hb"
                                    ws.send(frame.SerializeToString(), opcode=0x02)
                                    time.sleep(5)
                                except Exception as e:
                                    self.append_text_signal.emit(f"Ping失败: {str(e)}")
                                    break
                        
                        threading.Thread(target=ping, daemon=True).start()
                    
                    # 重写on_error方法
                    def qt_on_error(ws, error):
                        self.append_text_signal.emit(f"WebSocket错误: {str(error)}")
                    
                    # 重写on_close方法
                    def qt_on_close(ws, close_status_code, close_msg):
                        self.append_text_signal.emit("WebSocket连接已关闭")
                    
                    # 替换方法
                    live_monitor.on_message = qt_on_message
                    live_monitor.on_open = qt_on_open
                    live_monitor.on_error = qt_on_error
                    live_monitor.on_close = qt_on_close
                    
                    # 在单独线程中启动WebSocket连接
                    import threading
                    def run_websocket():
                        try:
                            # 使用信号发送到主线程更新UI
                            self.append_text_signal.emit("正在建立WebSocket连接...")
                            
                            # 启动WebSocket连接
                            live_monitor.start_ws()
                            
                        except KeyboardInterrupt:
                            self.append_text_signal.emit("WebSocket连接被用户中断")
                        except Exception as e:
                            error_msg = f"WebSocket运行错误: {str(e)}"
                            self.append_text_signal.emit(error_msg)
                            logger.error(f"WebSocket错误: {e}")
                            
                            # 使用信号发送到主线程重置按钮状态
                            from PyQt5.QtCore import QMetaObject, Qt
                            QMetaObject.invokeMethod(self, "reset_live_monitor_buttons", 
                                                   Qt.QueuedConnection)
                    
                    websocket_thread = threading.Thread(target=run_websocket, daemon=True)
                    websocket_thread.start()
                    
                    # 不等待线程完成，让主线程继续运行
                    return
                    
                else:
                    self.live_monitor_text.append("直播间当前未开播，无法监听")
            else:
                self.live_monitor_text.append("无法获取直播间信息")
                
        except Exception as e:
            self.live_monitor_text.append(f"监听失败: {str(e)}")
            raise e
    
    def on_live_monitor_finished(self, result):
        """直播间监听完成"""
        # 只有在没有WebSocket连接时才重置按钮状态
        if not self.live_monitor_ws:
            self.live_monitor_btn.setEnabled(True)
            self.live_monitor_btn.setText("开始监听")
            self.live_monitor_stop_btn.setEnabled(False)
            self.statusBar().showMessage("直播间监听完成")
    
    def append_live_monitor_text(self, text):
        """线程安全地添加文本到直播间监听显示区域"""
        try:
            self.live_monitor_text.append(text)
        except Exception as e:
            logger.error(f"添加监听文本失败: {e}")
    
    def reset_live_monitor_buttons(self):
        """重置直播间监听按钮状态"""
        try:
            self.live_monitor_btn.setEnabled(True)
            self.live_monitor_btn.setText("开始监听")
            self.live_monitor_stop_btn.setEnabled(False)
            self.live_monitor_ws = None
        except Exception as e:
            logger.error(f"重置按钮状态失败: {e}")
    
    def stop_live_monitor(self):
        """停止直播间监听"""
        try:
            if self.live_monitor_ws and hasattr(self.live_monitor_ws, 'ws') and self.live_monitor_ws.ws:
                self.live_monitor_ws.ws.close()
                self.live_monitor_text.append("已停止监听")
            
            # 重置按钮状态
            self.reset_live_monitor_buttons()
            
        except Exception as e:
            self.live_monitor_text.append(f"停止监听时出错: {str(e)}")
            self.reset_live_monitor_buttons()
    
    def save_live_monitor_data(self):
        """保存直播间监听数据"""
        if not self.live_monitor_data:
            QMessageBox.information(self, "提示", "没有监听数据可保存")
            return
        
        try:
            import os
            import json
            from datetime import datetime
            
            # 创建保存目录
            save_dir = os.path.join(os.getcwd(), 'datas', 'live_monitor')
            os.makedirs(save_dir, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            live_id = self.live_monitor_id.text().strip()
            json_filename = f"live_monitor_{live_id}_{timestamp}.json"
            excel_filename = f"live_monitor_{live_id}_{timestamp}.xlsx"
            
            json_path = os.path.join(save_dir, json_filename)
            excel_path = os.path.join(save_dir, excel_filename)
            
            # 保存JSON文件
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(self.live_monitor_data, f, ensure_ascii=False, indent=2)
            
            # 保存Excel文件
            import pandas as pd
            df = pd.DataFrame(self.live_monitor_data)
            df.to_excel(excel_path, index=False, engine='openpyxl')
            
            QMessageBox.information(self, "保存成功", 
                                  f"监听数据已保存到:\nJSON: {json_path}\nExcel: {excel_path}")
            
            self.live_monitor_text.append(f"数据已保存: {len(self.live_monitor_data)} 条记录")
            
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存数据时出错: {str(e)}")
            logger.error(f"保存直播间监听数据失败: {e}")
    
    def search_users(self):
        """搜索用户"""
        keyword = self.search_users_keyword.text().strip()
        count = self.search_users_count.text().strip()
        
        if not keyword:
            QMessageBox.warning(self, "输入错误", "请输入搜索关键词")
            return
        
        try:
            count = int(count) if count else 20
        except ValueError:
            QMessageBox.warning(self, "输入错误", "请输入有效的数量")
            return
        
        self.search_users_btn.setEnabled(False)
        self.search_users_btn.setText("搜索中...")
        
        # 创建工作线程
        self.worker = WorkerThread(self.data_spider.douyin_apis.search_some_user, 
                                 self.auth, keyword, count)
        self.worker.finished.connect(self.on_search_users_finished)
        self.worker.error.connect(self.on_worker_error)
        self.worker.start()
    
    def on_search_users_finished(self, result):
        """用户搜索完成"""
        self.search_users_data = result
        self.search_users_table.load_data(result, "search_users")
        
        # 自动保存到默认位置
        self.auto_save_data("search_users", result)
        
        self.search_users_btn.setEnabled(True)
        self.search_users_btn.setText("开始搜索")
        self.statusBar().showMessage(f"用户搜索完成，找到 {len(result)} 个结果")
    
    def search_live_rooms(self):
        """搜索直播间"""
        keyword = self.search_live_keyword.text().strip()
        count = self.search_live_count.text().strip()
        
        if not keyword:
            QMessageBox.warning(self, "输入错误", "请输入搜索关键词")
            return
        
        try:
            count = int(count) if count else 20
        except ValueError:
            QMessageBox.warning(self, "输入错误", "请输入有效的数量")
            return
        
        self.search_live_btn.setEnabled(False)
        self.search_live_btn.setText("搜索中...")
        
        # 创建工作线程
        self.worker = WorkerThread(self.data_spider.douyin_apis.search_some_live, 
                                 self.auth, keyword, count)
        self.worker.finished.connect(self.on_search_live_finished)
        self.worker.error.connect(self.on_worker_error)
        self.worker.start()
    
    def on_search_live_finished(self, result):
        """直播间搜索完成"""
        self.search_live_data = result
        self.search_live_table.load_data(result, "search_live")
        
        # 自动保存到默认位置
        self.auto_save_data("search_live", result)
        
        self.search_live_btn.setEnabled(True)
        self.search_live_btn.setText("开始搜索")
        self.statusBar().showMessage(f"直播间搜索完成，找到 {len(result)} 个结果")
    
    def on_worker_error(self, error_msg):
        """工作线程错误处理"""
        # 检查是否是KeyboardInterrupt错误
        if "KeyboardInterrupt" in str(error_msg):
            QMessageBox.warning(self, "操作中断", "用户中断了操作")
            self.statusBar().showMessage("操作被用户中断")
        else:
            QMessageBox.critical(self, "错误", f"操作失败: {error_msg}")
            self.statusBar().showMessage("操作失败")
        
        # 重置所有按钮状态
        self.reset_all_buttons()
    
    def auto_save_data(self, data_type, data):
        """自动保存数据到默认位置"""
        try:
            # 创建保存目录
            save_dir = os.path.join(os.getcwd(), 'datas', data_type)
            os.makedirs(save_dir, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_filename = f"{data_type}_{timestamp}.json"
            excel_filename = f"{data_type}_{timestamp}.xlsx"
            
            json_path = os.path.join(save_dir, json_filename)
            excel_path = os.path.join(save_dir, excel_filename)
            
            # 保存JSON文件
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 保存Excel文件
            if isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                df = pd.DataFrame([data])
            df.to_excel(excel_path, index=False, engine='openpyxl')
            
            # 下载媒体文件（视频和图片）
            self.download_media_files(data_type, data)
            
            # 存储文件路径供复制使用
            if not hasattr(self, 'saved_files'):
                self.saved_files = {}
            self.saved_files[data_type] = {
                'json_path': json_path,
                'excel_path': excel_path,
                'data': data
            }
            
            self.statusBar().showMessage(f"数据和媒体文件已自动保存到: {save_dir}")
            logger.info(f"数据已自动保存: {json_path}, {excel_path}")
            
        except Exception as e:
            logger.error(f"自动保存失败: {e}")
            self.statusBar().showMessage(f"自动保存失败: {str(e)}")
    
    def download_media_files(self, data_type, data):
        """下载媒体文件"""
        try:
            from utils.data_util import download_work, handle_work_info
            
            # 创建媒体保存目录
            media_dir = os.path.join(os.getcwd(), 'datas', 'media_datas')
            os.makedirs(media_dir, exist_ok=True)
            
            if isinstance(data, list):
                # 处理列表数据
                for item in data:
                    if isinstance(item, dict) and 'work_url' in item:
                        try:
                            # 重新处理数据以确保包含原始媒体信息
                            processed_item = self.prepare_work_info_for_download(item)
                            if processed_item:
                                download_work(processed_item, media_dir, 'media')
                                logger.debug(f"下载媒体文件: {item.get('title', 'Unknown')}")
                        except Exception as e:
                            logger.error(f"下载媒体文件失败: {e}")
            elif isinstance(data, dict) and 'work_url' in data:
                # 处理单个数据
                try:
                    processed_data = self.prepare_work_info_for_download(data)
                    if processed_data:
                        download_work(processed_data, media_dir, 'media')
                        logger.debug(f"下载媒体文件: {data.get('title', 'Unknown')}")
                except Exception as e:
                    logger.error(f"下载媒体文件失败: {e}")
                    
        except Exception as e:
            logger.error(f"下载媒体文件过程出错: {e}")
    
    def prepare_work_info_for_download(self, work_info):
        """准备用于下载的工作信息"""
        try:
            # 如果有原始数据，使用原始数据重新处理
            if 'raw_data' in work_info:
                from utils.data_util import handle_work_info
                raw_data = work_info['raw_data']
                processed_info = handle_work_info(raw_data)
                
                # 确保images是列表格式
                if 'images' in processed_info and isinstance(processed_info['images'], str):
                    if processed_info['images']:
                        processed_info['images'] = processed_info['images'].split('; ')
                    else:
                        processed_info['images'] = []
                
                return processed_info
            else:
                # 如果没有原始数据，尝试修复现有数据
                if 'images' in work_info and isinstance(work_info['images'], str):
                    if work_info['images']:
                        work_info['images'] = work_info['images'].split('; ')
                    else:
                        work_info['images'] = []
                
                # 确保必要字段存在
                required_fields = ['work_id', 'work_type', 'video_addr', 'video_cover']
                for field in required_fields:
                    if field not in work_info:
                        logger.warning(f"缺少必要字段 {field}，跳过下载")
                        return None
                
                return work_info
        except Exception as e:
            logger.error(f"准备下载数据失败: {e}")
            return None
    
    def save_data(self, data_type):
        """复制数据到其他位置"""
        if not hasattr(self, 'saved_files') or data_type not in self.saved_files:
            QMessageBox.warning(self, "保存错误", "没有找到已保存的数据，请先执行爬取操作")
            return
        
        saved_info = self.saved_files[data_type]
        
        # 选择保存路径
        default_dir = os.path.join(os.getcwd(), 'datas')
        os.makedirs(default_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"{data_type}_copy_{timestamp}.json"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "复制数据到其他位置", 
            os.path.join(default_dir, default_filename),
            "JSON文件 (*.json);;Excel文件 (*.xlsx);;所有文件 (*)"
        )
        
        if file_path:
            try:
                if file_path.endswith('.xlsx'):
                    # 复制Excel文件
                    import shutil
                    shutil.copy2(saved_info['excel_path'], file_path)
                else:
                    # 复制JSON文件
                    import shutil
                    shutil.copy2(saved_info['json_path'], file_path)
                
                QMessageBox.information(self, "复制成功", f"数据已复制到: {file_path}")
                self.statusBar().showMessage(f"数据已复制到: {os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.critical(self, "复制失败", f"复制数据时出错: {str(e)}")
    
    def filter_keywords(self):
        """关键词筛选功能"""
        keyword = self.keyword_input.text().strip()
        if not keyword:
            QMessageBox.warning(self, "输入错误", "请输入关键词")
            return
        
        data_type = self.data_type_combo.currentText()
        
        # 清空进度显示
        self.filter_progress.clear()
        self.filter_progress.append(f"🔍 开始筛选关键词: {keyword}")
        self.filter_progress.append(f"📊 数据类型: {data_type}")
        self.filter_progress.append("⏳ 正在扫描数据文件...")
        
        # 禁用按钮
        self.filter_btn.setEnabled(False)
        self.filter_btn.setText("筛选中...")
        
        try:
            if data_type == "评论数据":
                self.filter_comments_data(keyword)
            elif data_type == "直播监听数据":
                self.filter_live_data(keyword)
        except Exception as e:
            QMessageBox.critical(self, "筛选失败", f"筛选过程中出错: {str(e)}")
            self.filter_btn.setEnabled(True)
            self.filter_btn.setText("开始筛选")
    
    def filter_comments_data(self, keyword):
        """筛选评论数据"""
        comments_dir = os.path.join(os.getcwd(), 'datas', 'comments')
        if not os.path.exists(comments_dir):
            self.filter_progress.append("❌ 评论数据目录不存在")
            self.filter_btn.setEnabled(True)
            self.filter_btn.setText("开始筛选")
            return
        
        # 获取所有JSON文件
        json_files = [f for f in os.listdir(comments_dir) if f.endswith('.json')]
        if not json_files:
            self.filter_progress.append("❌ 未找到评论数据文件")
            self.filter_btn.setEnabled(True)
            self.filter_btn.setText("开始筛选")
            return
        
        self.filter_progress.append(f"📁 找到 {len(json_files)} 个评论数据文件")
        
        filtered_results = []
        total_processed = 0
        
        for json_file in json_files:
            file_path = os.path.join(comments_dir, json_file)
            self.filter_progress.append(f"📄 正在处理: {json_file}")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if isinstance(data, list):
                    for item in data:
                        total_processed += 1
                        text = item.get('text', '')
                        user_info = item.get('user', {})
                        sec_uid = user_info.get('sec_uid', '')
                        
                        if keyword in text and sec_uid:
                            user_url = f"https://www.douyin.com/user/{sec_uid}"
                            filtered_results.append({
                                'text': text,
                                'user_url': user_url
                            })
                
                self.filter_progress.append(f"✅ 处理完成: {json_file}")
                
            except Exception as e:
                self.filter_progress.append(f"❌ 处理失败: {json_file} - {str(e)}")
        
        self.display_filter_results(filtered_results, total_processed, keyword)
    
    def filter_live_data(self, keyword):
        """筛选直播监听数据"""
        live_dir = os.path.join(os.getcwd(), 'datas', 'live_monitor')
        if not os.path.exists(live_dir):
            self.filter_progress.append("❌ 直播监听数据目录不存在")
            self.filter_btn.setEnabled(True)
            self.filter_btn.setText("开始筛选")
            return
        
        # 获取所有JSON文件
        json_files = [f for f in os.listdir(live_dir) if f.endswith('.json')]
        if not json_files:
            self.filter_progress.append("❌ 未找到直播监听数据文件")
            self.filter_btn.setEnabled(True)
            self.filter_btn.setText("开始筛选")
            return
        
        self.filter_progress.append(f"📁 找到 {len(json_files)} 个直播监听数据文件")
        
        filtered_results = []
        total_processed = 0
        
        for json_file in json_files:
            file_path = os.path.join(live_dir, json_file)
            self.filter_progress.append(f"📄 正在处理: {json_file}")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if isinstance(data, list):
                    for item in data:
                        total_processed += 1
                        content = item.get('content', '')
                        user_sec_uid = item.get('user_sec_uid', '')
                        
                        if keyword in content and user_sec_uid:
                            user_url = f"https://www.douyin.com/user/{user_sec_uid}"
                            filtered_results.append({
                                'text': content,
                                'user_url': user_url
                            })
                
                self.filter_progress.append(f"✅ 处理完成: {json_file}")
                
            except Exception as e:
                self.filter_progress.append(f"❌ 处理失败: {json_file} - {str(e)}")
        
        self.display_filter_results(filtered_results, total_processed, keyword)
    
    def display_filter_results(self, results, total_processed, keyword):
        """显示筛选结果"""
        self.filter_data = results
        
        # 更新进度显示
        self.filter_progress.append(f"✅ 筛选完成！")
        self.filter_progress.append(f"📊 总共处理: {total_processed} 条数据")
        self.filter_progress.append(f"🎯 匹配关键词 '{keyword}': {len(results)} 条")
        
        if results:
            self.filter_progress.append(f"📋 正在显示结果...")
            
            # 显示结果表格
            self.filter_table.setRowCount(len(results))
            for row, item in enumerate(results):
                self.filter_table.setItem(row, 0, QTableWidgetItem(item['text'][:100] + '...' if len(item['text']) > 100 else item['text']))
                self.filter_table.setItem(row, 1, QTableWidgetItem(item['user_url']))
            
            self.filter_table.resizeColumnsToContents()
            self.filter_progress.append(f"📋 结果已显示在表格中")
        else:
            self.filter_progress.append("⚠️ 未找到匹配的数据")
        
        # 自动保存筛选结果
        if results:
            self.auto_save_filter_results(results, keyword)
        
        # 恢复按钮状态
        self.filter_btn.setEnabled(True)
        self.filter_btn.setText("开始筛选")
    
    def auto_save_filter_results(self, results, keyword):
        """自动保存筛选结果到keyword_filter目录"""
        try:
            # 创建保存目录
            save_dir = os.path.join(os.getcwd(), 'datas', 'keyword_filter')
            os.makedirs(save_dir, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_keyword = "".join(c for c in keyword if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"keyword_filter_{safe_keyword}_{timestamp}.json"
            file_path = os.path.join(save_dir, filename)
            
            # 保存JSON文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            # 保存Excel文件
            excel_filename = f"keyword_filter_{safe_keyword}_{timestamp}.xlsx"
            excel_path = os.path.join(save_dir, excel_filename)
            
            df = pd.DataFrame(results)
            df.to_excel(excel_path, index=False, engine='openpyxl')
            
            # 更新进度显示
            self.filter_progress.append(f"💾 筛选结果已自动保存:")
            self.filter_progress.append(f"   📄 JSON: {filename}")
            self.filter_progress.append(f"   📊 Excel: {excel_filename}")
            
            # 更新状态栏
            self.statusBar().showMessage(f"筛选结果已保存: {filename}")
            
        except Exception as e:
            self.filter_progress.append(f"❌ 自动保存失败: {str(e)}")
    
    def save_filter_results(self):
        """保存筛选结果"""
        if not self.filter_data:
            QMessageBox.warning(self, "保存错误", "没有筛选结果可保存")
            return
        
        # 选择保存路径
        default_dir = os.path.join(os.getcwd(), 'datas', 'keyword_filter')
        os.makedirs(default_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        keyword = self.keyword_input.text().strip()
        safe_keyword = "".join(c for c in keyword if c.isalnum() or c in (' ', '-', '_')).rstrip()
        
        default_filename = f"keyword_filter_{safe_keyword}_{timestamp}.json"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存筛选结果", 
            os.path.join(default_dir, default_filename),
            "JSON文件 (*.json);;Excel文件 (*.xlsx);;所有文件 (*)"
        )
        
        if file_path:
            try:
                if file_path.endswith('.xlsx'):
                    # 保存为Excel文件
                    df = pd.DataFrame(self.filter_data)
                    df.to_excel(file_path, index=False, engine='openpyxl')
                else:
                    # 保存为JSON文件
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(self.filter_data, f, ensure_ascii=False, indent=2)
                
                QMessageBox.information(self, "保存成功", f"筛选结果已保存到: {file_path}")
                self.statusBar().showMessage(f"筛选结果已保存: {os.path.basename(file_path)}")
                
                # 更新进度显示
                self.filter_progress.append(f"💾 结果已保存到: {os.path.basename(file_path)}")
                
            except Exception as e:
                QMessageBox.critical(self, "保存失败", f"保存筛选结果时出错: {str(e)}")
    
    def start_trace_function(self):
        """开始留痕功能"""
        try:
            visit_count = int(self.visit_count_input.text().strip())
            if visit_count < 2 or visit_count > 5:
                QMessageBox.warning(self, "输入错误", "访问次数必须在2-5次之间")
                return
        except ValueError:
            QMessageBox.warning(self, "输入错误", "请输入有效的数字")
            return
        
        # 清空进度显示
        self.trace_progress.clear()
        self.trace_progress.append(f"🔍 开始留痕功能")
        self.trace_progress.append(f"📊 访问次数: {visit_count}")
        self.trace_progress.append("⏳ 正在扫描关键词筛选结果...")
        
        # 禁用按钮
        self.trace_btn.setEnabled(False)
        self.trace_btn.setText("留痕中...")
        
        try:
            # 扫描keyword_filter目录下的所有JSON文件
            keyword_filter_dir = os.path.join("datas", "keyword_filter")
            if not os.path.exists(keyword_filter_dir):
                QMessageBox.warning(self, "目录不存在", f"关键词筛选目录不存在: {keyword_filter_dir}")
                self.trace_btn.setEnabled(True)
                self.trace_btn.setText("开始留痕")
                return
            
            # 获取所有JSON文件
            json_files = [f for f in os.listdir(keyword_filter_dir) if f.endswith('.json')]
            if not json_files:
                QMessageBox.warning(self, "无数据", "关键词筛选目录下没有JSON文件")
                self.trace_btn.setEnabled(True)
                self.trace_btn.setText("开始留痕")
                return
            
            self.trace_progress.append(f"📁 找到 {len(json_files)} 个JSON文件")
            
            # 收集所有用户链接
            all_user_urls = []
            for json_file in json_files:
                file_path = os.path.join(keyword_filter_dir, json_file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            for item in data:
                                if isinstance(item, dict) and 'user_url' in item:
                                    all_user_urls.append({
                                        'text': item.get('text', ''),
                                        'user_url': item['user_url']
                                    })
                except Exception as e:
                    self.trace_progress.append(f"⚠️ 读取文件失败 {json_file}: {str(e)}")
                    continue
            
            if not all_user_urls:
                QMessageBox.warning(self, "无数据", "没有找到有效的用户链接")
                self.trace_btn.setEnabled(True)
                self.trace_btn.setText("开始留痕")
                return
            
            self.trace_progress.append(f"🔗 找到 {len(all_user_urls)} 个用户链接")
            self.trace_progress.append("🌐 开始访问用户链接...")
            
            # 开始访问链接
            self.trace_data = []
            successful_visits = 0
            failed_visits = 0
            
            for i, item in enumerate(all_user_urls):
                user_url = item['user_url']
                text = item['text']
                
                self.trace_progress.append(f"📱 正在访问 ({i+1}/{len(all_user_urls)}): {user_url}")
                
                # 随机访问次数
                actual_visits = random.randint(2, visit_count)
                visit_success = 0
                
                for visit in range(actual_visits):
                    try:
                        # 使用requests访问链接
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                        }
                        response = requests.get(user_url, headers=headers, timeout=10)
                        if response.status_code == 200:
                            visit_success += 1
                        else:
                            self.trace_progress.append(f"  ⚠️ 访问失败 (状态码: {response.status_code})")
                    except Exception as e:
                        self.trace_progress.append(f"  ❌ 访问异常: {str(e)}")
                    
                    # 随机延迟，避免请求过快
                    time.sleep(random.uniform(1, 3))
                
                # 记录结果
                self.trace_data.append({
                    'text': text,
                    'user_url': user_url,
                    'visit_count': visit_success
                })
                
                if visit_success > 0:
                    successful_visits += 1
                    self.trace_progress.append(f"  ✅ 成功访问 {visit_success}/{actual_visits} 次")
                else:
                    failed_visits += 1
                    self.trace_progress.append(f"  ❌ 访问失败")
            
            # 显示结果
            self.trace_table.load_data(self.trace_data, "trace")
            
            # 显示统计信息
            self.trace_progress.append(f"🎉 留痕功能完成！")
            self.trace_progress.append(f"📊 总链接数: {len(all_user_urls)}")
            self.trace_progress.append(f"✅ 成功访问: {successful_visits}")
            self.trace_progress.append(f"❌ 访问失败: {failed_visits}")
            self.trace_progress.append(f"📈 成功率: {successful_visits/len(all_user_urls)*100:.1f}%")
            
            # 自动保存结果
            self.auto_save_data("trace", self.trace_data)
            
            self.statusBar().showMessage(f"留痕功能完成，处理了 {len(all_user_urls)} 个链接")
            
        except Exception as e:
            QMessageBox.critical(self, "留痕失败", f"留痕功能执行失败: {str(e)}")
            self.trace_progress.append(f"❌ 留痕功能失败: {str(e)}")
        finally:
            # 恢复按钮状态
            self.trace_btn.setEnabled(True)
            self.trace_btn.setText("开始留痕")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("抖音爬虫工具")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("五更琉璃")
    
    # 设置Qt应用程序属性，减少警告（必须在创建QApplication之前设置）
    try:
        from PyQt5.QtCore import Qt
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    except Exception as e:
        logger.warning(f"设置Qt属性失败: {e}")
    
    # 注册Qt类型，避免信号队列错误
    try:
        from PyQt5.QtCore import qRegisterMetaType
        from PyQt5.QtGui import QTextCursor
        # 注册QTextCursor类型
        qRegisterMetaType("QTextCursor")
    except Exception as e:
        logger.warning(f"注册Qt类型失败: {e}")
    
    # 创建主窗口
    try:
        window = DouyinSpiderGUI()
        window.show()
        
        sys.exit(app.exec_())
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        QMessageBox.critical(None, "启动错误", f"应用启动失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
