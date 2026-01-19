# -*- coding: utf-8 -*-
# 豆瓣电影讨论爬虫配置

# 豆瓣电影讨论URL列表
# 格式：https://movie.douban.com/subject/{电影ID}/discussion/?start=0&sort_by=time
DOUBAN_DISCUSSION_URL_LIST = [
    "https://movie.douban.com/subject/36035676/discussion/?start=0&sort_by=time",  # 流浪地球2
    # "https://movie.douban.com/subject/35725869/discussion/?start=0&sort_by=time",  # 消失的她
    # "https://movie.douban.com/subject/35943560/discussion/?start=0&sort_by=time",  # 长安三万里
    # "https://movie.douban.com/subject/35766477/discussion/?start=0&sort_by=time",  # 封神第一部
    # "https://movie.douban.com/subject/35749412/discussion/?start=0&sort_by=time",  # 孤注一掷
]

# 爬取控制
DOUBAN_CRAWLER_MAX_DISCUSSIONS = 100  # 最多爬取多少个讨论
DOUBAN_CRAWLER_MAX_REPLIES = 200  # 每个讨论最多爬取多少条回复

# 是否爬取图片URL
DOUBAN_ENABLE_GET_IMAGES = True

# 爬取间隔（秒）
DOUBAN_CRAWLER_SLEEP_SEC = 3
