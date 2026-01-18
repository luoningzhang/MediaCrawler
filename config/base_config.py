# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/config/base_config.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#

# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：
# 1. 不得用于任何商业用途。
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。
# 3. 不得进行大规模爬取或对平台造成运营干扰。
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。
# 5. 不得用于任何非法或不当的用途。
#
# 详细许可条款请参阅项目根目录下的LICENSE文件。
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。

# ==================== 基础配置 ====================
# 🎬 电影研究专用配置 - 中国电影观众传播影响力研究
# 研究对象：《流浪地球2》《消失的她》《长安三万里》《封神第一部》《孤注一掷》

PLATFORM = "xhs"  # 平台选择: xhs(小红书) | dy(抖音) | wb(微博)
KEYWORDS = "流浪地球2"  # 关键词搜索配置（建议一次爬一部电影）
LOGIN_TYPE = "qrcode"  # 登录方式: qrcode(二维码) | phone(手机) | cookie
COOKIES = ""
CRAWLER_TYPE = "search"  # 爬取类型: search(关键词搜索) | detail(帖子详情) | creator(创作者主页)

# 是否开启 IP 代理（建议关闭，避免配置复杂度）
ENABLE_IP_PROXY = False

# 代理IP池数量
IP_PROXY_POOL_COUNT = 2

# 代理IP提供商名称
IP_PROXY_PROVIDER_NAME = "kuaidaili"  # kuaidaili | wandouhttp

# 是否使用无头浏览器模式
# False = 打开浏览器窗口（推荐用于首次登录和调试）
# True = 后台运行（需要先完成登录保存状态）
HEADLESS = False

# 是否保存登录状态（强烈建议开启，避免重复登录）
SAVE_LOGIN_STATE = True

# ==================== CDP (Chrome DevTools Protocol) 配置 ====================
# 是否启用CDP模式 - 使用用户现有的Chrome/Edge浏览器进行爬取，提供更好的反检测能力
# 启用后将自动检测并启动用户的Chrome/Edge浏览器，通过CDP协议进行控制
# 这种方式使用真实的浏览器环境，包括用户的扩展、Cookie和设置，大大降低被检测的风险
ENABLE_CDP_MODE = True

# CDP调试端口，用于与浏览器通信
# 如果端口被占用，系统会自动尝试下一个可用端口
CDP_DEBUG_PORT = 9222

# 自定义浏览器路径（可选）
# 如果为空，系统会自动检测Chrome/Edge的安装路径
# Windows示例: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
# macOS示例: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CUSTOM_BROWSER_PATH = ""

# CDP模式下是否启用无头模式
# 注意：即使设置为True，某些反检测功能在无头模式下可能效果不佳
CDP_HEADLESS = False

# 浏览器启动超时时间（秒）
BROWSER_LAUNCH_TIMEOUT = 60

# 是否在程序结束时自动关闭浏览器
# 设置为False可以保持浏览器运行，便于调试
AUTO_CLOSE_BROWSER = True

# ==================== 数据存储配置 ====================
# 数据保存格式：json(推荐) | csv | excel
# 注意：不使用数据库存储，所有数据保存在 data/ 目录下
SAVE_DATA_OPTION = "json"

# 用户浏览器缓存目录配置
USER_DATA_DIR = "%s_user_data_dir"  # %s 会被替换为平台名称 (xhs/dy/wb)

# ==================== 爬取控制参数 ====================
# 爬取开始页数（默认从第一页开始）
START_PAGE = 1

# 爬取笔记/视频的数量（建议增加以获取更多数据）
CRAWLER_MAX_NOTES_COUNT = 100

# 并发爬虫数量（建议设为1，避免被封）
MAX_CONCURRENCY_NUM = 1

# 是否下载媒体文件（图片/视频）- 建议关闭以节省空间
ENABLE_GET_MEIDAS = False

# ==================== 评论爬取配置 ====================
# 是否爬取评论（必须开启！评论是研究的核心数据）
ENABLE_GET_COMMENTS = True

# 每个笔记/视频爬取的一级评论数量（建议增加）
CRAWLER_MAX_COMMENTS_COUNT_SINGLENOTES = 50

# 是否爬取二级评论（建议开启，获取更完整的讨论数据）
ENABLE_GET_SUB_COMMENTS = True

# 词云相关
# 是否开启生成评论词云图
ENABLE_GET_WORDCLOUD = False
# 自定义词语及其分组
# 添加规则：xx:yy 其中xx为自定义添加的词组，yy为将xx该词组分到的组名。
CUSTOM_WORDS = {
    "零几": "年份",  # 将“零几”识别为一个整体
    "高频词": "专业术语",  # 示例自定义词
}

# 停用(禁用)词文件路径
STOP_WORDS_FILE = "./docs/hit_stopwords.txt"

# 中文字体文件路径
FONT_PATH = "./docs/STZHONGS.TTF"

# 爬取间隔时间
CRAWLER_MAX_SLEEP_SEC = 2

from .bilibili_config import *
from .xhs_config import *
from .dy_config import *
from .ks_config import *
from .weibo_config import *
from .tieba_config import *
from .zhihu_config import *
