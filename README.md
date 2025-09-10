# DouYin_Spider

**专业的抖音数据采集解决方案，支持视频爬取、用户信息获取、直播间监听等功能**

**作者：五更琉璃**  
**日期：2025年**

## 项目简介

本项目是一个功能完整的抖音数据采集工具，支持多种数据获取方式，包括视频信息爬取、用户作品获取、搜索功能、评论区数据采集以及直播间实时监听等。项目采用模块化设计，易于扩展和维护。

## 功能特性

### 核心功能
- **视频信息爬取**：获取单个视频的详细信息，包括标题、作者、点赞数、评论数等
- **用户作品批量获取**：爬取指定用户的所有作品信息
- **智能搜索**：支持关键词搜索视频，可设置排序方式和筛选条件
- **评论区数据采集**：获取视频的一级和二级评论数据
- **直播间监听**：实时监听直播间弹幕和礼物信息
- **用户搜索**：根据关键词搜索用户信息
- **直播间搜索**：搜索正在直播的直播间

### 技术特性
- **多维度数据采集**：支持视频、用户、评论、直播等多种数据类型
- **高性能架构**：采用异步处理和自动重试机制
- **安全稳定**：适配抖音最新API，具备完善的异常处理
- **便捷管理**：支持多种数据保存格式（JSON/EXCEL/MEDIA）
- **交互式控制台**：提供友好的命令行界面

## 项目结构

```
DouYin_Spider/
├── builder/                 # 构建器模块
│   ├── __init__.py
│   ├── auth.py             # 认证构建器
│   ├── header.py           # 请求头构建器
│   ├── params.py           # 参数构建器
│   └── proto.py            # 协议构建器
├── dy_apis/                # API接口模块
│   ├── __init__.py
│   └── douyin_api.py       # 抖音API接口
├── dy_live/                # 直播间模块
│   ├── __init__.py
│   └── server.py           # 直播间监听服务
├── static/                 # 静态资源
│   ├── dy_ab.js           # JavaScript文件
│   ├── dy_live_sign.js    # 直播签名文件
│   ├── Live_pb2.py        # 直播协议文件
│   ├── Live.proto         # 直播协议定义
│   ├── Request_pb2.py     # 请求协议文件
│   ├── Request.proto      # 请求协议定义
│   ├── Response_pb2.py    # 响应协议文件
│   └── Response.proto     # 响应协议定义
├── utils/                  # 工具模块
│   ├── __init__.py
│   ├── common_util.py     # 通用工具
│   ├── cookie_util.py     # Cookie工具
│   ├── data_util.py       # 数据处理工具
│   └── dy_util.py         # 抖音专用工具
├── console_interface.py    # 控制台界面
├── main.py                # 主程序入口
├── requirements.txt       # Python依赖
├── package.json          # Node.js依赖
├── Dockerfile            # Docker配置
└── README.md             # 项目说明
```

## 安装配置

### 环境要求
- Python 3.7+
- Node.js 18+

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd DouYin_Spider
```

2. **安装Python依赖**
```bash
pip install -r requirements.txt
```

3. **安装Node.js依赖**
```bash
npm install
```

4. **配置环境变量**
创建`.env`文件并配置以下内容：
```env
# 抖音主站Cookie（从www.douyin.com获取）
DOUYIN_COOKIE=your_douyin_cookie_here

# 直播间Cookie（从live.douyin.com获取）
LIVE_COOKIE=your_live_cookie_here
```

### Cookie获取方法

1. 打开浏览器，访问 `https://www.douyin.com`
2. 登录你的抖音账号
3. 按F12打开开发者工具
4. 切换到Network标签页
5. 刷新页面，找到任意一个请求
6. 复制请求头中的Cookie值
7. 将Cookie值填入`.env`文件

## 使用方法

### 交互式控制台

推荐使用交互式控制台，提供友好的用户界面：

```bash
python main.py --console
```

控制台提供以下功能：
1. 爬取单个视频信息
2. 爬取用户所有作品
3. 搜索视频
4. 爬取视频评论区
5. 监听直播间
6. 搜索用户
7. 搜索直播间

### 编程接口

#### 基本使用示例

```python
from main import Data_Spider
from utils.common_util import init

# 初始化
auth, base_path = init()
data_spider = Data_Spider()

# 爬取单个视频
video_url = "https://www.douyin.com/video/1234567890"
work_info = data_spider.spider_work(auth, video_url)
print(f"视频标题: {work_info['title']}")

# 爬取用户所有作品
user_url = "https://www.douyin.com/user/MS4wLjABAAAA..."
data_spider.spider_user_all_work(auth, user_url, base_path, 'all')

# 搜索视频
query = "美食"
require_num = 20
data_spider.spider_some_search_work(
    auth, query, require_num, base_path, 'all', 
    sort_type='0', publish_time='0'
)
```

#### 高级功能示例

```python
from dy_apis.douyin_api import DouyinAPI

# 获取视频所有评论
all_comments = DouyinAPI.get_work_all_comment(auth, video_url)
print(f"共获取到 {len(all_comments)} 条评论")

# 搜索用户
users = DouyinAPI.search_some_user(auth, "关键词", 10)
for user in users:
    print(f"用户: {user['user_info']['nickname']}")

# 监听直播间
live_info = DouyinAPI.get_live_info(auth, "直播间ID")
if live_info['room_status'] == '2':  # 直播中
    # 开始监听
    pass
```

## 核心代码说明

### 主要类和方法

#### Data_Spider类
```python
class Data_Spider:
    def __init__(self):
        """初始化爬虫实例"""
        self.douyin_apis = DouyinAPI()
    
    def spider_work(self, auth, work_url):
        """爬取单个作品信息"""
        # 获取作品详细信息
        # 处理数据格式
        # 返回结构化数据
    
    def spider_user_all_work(self, auth, user_url, base_path, save_choice):
        """爬取用户所有作品"""
        # 获取用户信息
        # 批量获取作品列表
        # 处理并保存数据
    
    def spider_some_search_work(self, auth, query, require_num, base_path, save_choice, sort_type, publish_time):
        """搜索指定数量的作品"""
        # 构建搜索参数
        # 执行搜索请求
        # 处理搜索结果
```

#### DouyinAPI类
```python
class DouyinAPI:
    @staticmethod
    def get_work_info(auth, url):
        """获取作品详细信息"""
        # 构建请求参数
        # 发送API请求
        # 返回JSON数据
    
    @staticmethod
    def get_work_all_comment(auth, url):
        """获取作品所有评论"""
        # 获取一级评论
        # 获取二级评论
        # 合并评论数据
    
    @staticmethod
    def search_some_general_work(auth, query, num, sort_type, publish_time):
        """搜索综合频道作品"""
        # 构建搜索参数
        # 执行搜索
        # 返回作品列表
```

### 数据处理流程

1. **认证初始化**：加载Cookie和配置信息
2. **请求构建**：根据API要求构建请求头和参数
3. **数据获取**：发送HTTP请求获取原始数据
4. **数据解析**：解析JSON响应，提取关键信息
5. **数据存储**：根据用户选择保存为不同格式

### 错误处理机制

```python
try:
    # API调用
    result = DouyinAPI.get_work_info(auth, url)
except Exception as e:
    logger.error(f"获取作品信息失败: {e}")
    # 错误处理逻辑
```

## 配置说明

### 保存选项
- `all`：保存所有信息（媒体文件+Excel）
- `media`：只保存媒体文件（视频/图片）
- `excel`：只保存Excel文件
- `media-video`：只下载视频
- `media-image`：只下载图片

### 搜索参数
- **排序方式**：0-综合排序，1-最多点赞，2-最新发布
- **发布时间**：0-不限，1-一天内，7-一周内，180-半年内
- **视频时长**：空-不限，0-1-一分钟内，1-5-1-5分钟，5-10000-5分钟以上

## 注意事项

1. **Cookie有效性**：Cookie会过期，需要定期更新
2. **请求频率**：避免过于频繁的请求，建议添加延时
3. **数据合规**：仅用于学习研究，不得用于商业用途
4. **网络环境**：确保网络连接稳定，必要时使用代理
5. **版本兼容**：定期更新以适配抖音API变化

## 常见问题

### Q: Cookie获取失败怎么办？
A: 确保已登录抖音账号，清除浏览器缓存后重新获取

### Q: 请求返回空数据？
A: 检查Cookie是否有效，URL是否正确，网络是否正常

### Q: 如何提高爬取效率？
A: 可以调整请求间隔，使用多线程，或配置代理

### Q: 直播间监听连接失败？
A: 检查直播间ID是否正确，直播间是否正在直播

## 更新日志

| 日期 | 版本 | 说明 |
|------|------|------|
| 2025-01-01 | v2.0.0 | 重构项目架构，添加交互式控制台 |
| 2025-01-01 | v2.0.0 | 更新作者信息，优化代码结构 |
| 2025-01-01 | v2.0.0 | 完善文档和注释 |

## 许可证

本项目仅供学习交流使用，请勿用于商业用途。使用本项目产生的任何问题，作者不承担责任。

## 联系方式

如有问题或建议，欢迎通过以下方式联系：
- 提交Issue
- 发送邮件
- 微信交流

---

**感谢使用DouYin_Spider！**
