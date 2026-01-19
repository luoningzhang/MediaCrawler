#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
豆瓣电影讨论爬虫 - 手动版（无需 Playwright/Selenium）
只需要 requests 和 beautifulsoup4

使用方法：
1. 先在浏览器中登录豆瓣
2. 按 F12 打开开发者工具
3. 刷新页面，在 Network 标签找到讨论页面的请求
4. 右键 -> Copy -> Copy as cURL
5. 将 Cookie 粘贴到下面的 COOKIES 变量中

安装依赖：
pip install requests beautifulsoup4 lxml
"""

import requests
import json
import time
import re
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup

# ==================== 配置区域 ====================

# Cookie（可选！豆瓣讨论大部分内容不登录也能访问）
# 如果爬取失败提示需要登录，再添加 Cookie
# 获取方法：浏览器登录豆瓣 -> F12 -> Network -> 刷新 -> 找到请求 -> Headers -> Cookie
COOKIES = """
"""
# 留空即可！如果遇到限制再填写

# 豆瓣电影讨论URL
DOUBAN_DISCUSSION_URL = "https://movie.douban.com/subject/36035676/discussion/?start=0&sort_by=time"

# 电影名称
MOVIE_NAME = "流浪地球2"

# 爬取控制
MAX_DISCUSSIONS = 50  # 最多爬取多少个讨论
MAX_REPLIES = 100     # 每个讨论最多爬取多少条回复
SLEEP_SECONDS = 2     # 请求间隔

# 数据保存目录
DATA_DIR = Path("data/douban/json")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ==================== 爬虫类 ====================

class ManualDoubanCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.setup_session()
        self.discussions = []
        self.all_replies = []

    def setup_session(self):
        """设置请求头"""
        # 解析 Cookie 字符串
        cookie_dict = {}
        if COOKIES.strip():
            for item in COOKIES.strip().split(';'):
                if '=' in item:
                    key, value = item.strip().split('=', 1)
                    cookie_dict[key] = value

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.douban.com/',
        }

        self.session.headers.update(headers)
        self.session.cookies.update(cookie_dict)

    def get_page(self, url):
        """获取页面内容"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response.text
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return None

    def get_discussion_list(self):
        """获取讨论列表"""
        print(f"\n📋 开始爬取讨论列表...")

        discussions = []
        page = 1
        current_url = DOUBAN_DISCUSSION_URL

        while len(discussions) < MAX_DISCUSSIONS:
            print(f"\n📄 正在爬取第 {page} 页...")

            html = self.get_page(current_url)
            if not html:
                print("⚠️  获取页面失败")
                break

            # 检查是否需要登录
            if '登录豆瓣' in html or 'login.douban.com' in html:
                print("\n❌ 需要登录！请按照以下步骤操作：")
                print("1. 在浏览器中登录豆瓣")
                print("2. 按 F12 打开开发者工具")
                print("3. 刷新页面，在 Network 标签找到讨论页面的请求")
                print("4. 右键 -> Copy -> Copy as cURL (bash)")
                print("5. 在其中找到 Cookie 部分，复制到本脚本的 COOKIES 变量中")
                return []

            soup = BeautifulSoup(html, 'lxml')
            topics = soup.find_all('tr', class_='topic')

            if not topics:
                print("⚠️  没有找到讨论")
                break

            for topic in topics:
                try:
                    # 标题和链接
                    title_elem = topic.find('td', class_='title')
                    if title_elem:
                        link = title_elem.find('a')
                        title = link.get_text(strip=True) if link else ""
                        url = link['href'] if link and link.has_attr('href') else ""
                    else:
                        continue

                    # 作者
                    author_elem = topic.find('td', class_='td-author')
                    author = author_elem.find('a').get_text(strip=True) if author_elem and author_elem.find('a') else "未知"

                    # 回复数
                    reply_elem = topic.find('td', class_='r-count')
                    reply_text = reply_elem.get_text(strip=True) if reply_elem else "0"
                    reply_count = int(reply_text) if reply_text.isdigit() else 0

                    # 时间
                    time_elem = topic.find('td', class_='time')
                    last_reply_time = time_elem.get_text(strip=True) if time_elem else ""

                    discussion_id = url.split('/')[-2] if url else ""

                    discussion = {
                        'discussion_id': discussion_id,
                        'title': title,
                        'url': url,
                        'author': author,
                        'reply_count': reply_count,
                        'last_reply_time': last_reply_time
                    }

                    discussions.append(discussion)
                    print(f"  ✅ [{len(discussions)}] {title[:50]}... (回复: {reply_count})")

                    if len(discussions) >= MAX_DISCUSSIONS:
                        break

                except Exception as e:
                    print(f"  ⚠️  解析讨论失败: {e}")
                    continue

            if len(discussions) >= MAX_DISCUSSIONS:
                break

            # 查找下一页
            next_link = soup.find('span', class_='next')
            if next_link and next_link.find('a'):
                next_url = next_link.find('a')['href']
                if next_url and 'javascript' not in next_url:
                    if not next_url.startswith('http'):
                        base_url = current_url.split('?')[0]
                        current_url = base_url + next_url if next_url.startswith('?') else base_url + '?' + next_url
                    else:
                        current_url = next_url
                    time.sleep(SLEEP_SECONDS)
                    page += 1
                else:
                    break
            else:
                print("📌 已到最后一页")
                break

        print(f"\n✅ 共爬取 {len(discussions)} 个讨论")
        return discussions

    def get_discussion_detail(self, discussion):
        """获取讨论详情"""
        url = discussion['url']
        print(f"\n💬 正在爬取: {discussion['title'][:50]}...")

        html = self.get_page(url)
        if not html:
            return discussion

        soup = BeautifulSoup(html, 'lxml')

        # 初始帖子内容
        content_elem = soup.find('div', id='link-report')
        if content_elem:
            topic_content = content_elem.find('div', class_='topic-content')
            content = topic_content.get_text(strip=True) if topic_content else ""

            # 获取图片
            images = []
            img_elems = content_elem.find_all('img')
            for img in img_elems:
                src = img.get('src', '')
                if src and 'icon' not in src:
                    images.append(src)

            discussion['content'] = content
            discussion['images'] = images

        # 发布时间
        time_elem = soup.find('span', class_='color-green')
        discussion['post_time'] = time_elem.get_text(strip=True) if time_elem else ""

        # 获取回复
        replies = []
        reply_items = soup.find_all('div', class_='reply-item') or soup.find_all('div', class_='comment-item')

        for idx, reply_elem in enumerate(reply_items):
            if idx >= MAX_REPLIES:
                break

            try:
                # 作者
                author_elem = reply_elem.find('a', class_='j') or reply_elem.find('span', class_='pubdate')
                if author_elem:
                    if author_elem.name == 'a':
                        reply_author = author_elem.get_text(strip=True)
                    else:
                        reply_author = author_elem.find('a').get_text(strip=True) if author_elem.find('a') else "未知"
                else:
                    reply_author = "未知"

                # 内容
                content_elem = reply_elem.find('p', class_='reply-content') or reply_elem.find('p')
                reply_content = content_elem.get_text(strip=True) if content_elem else ""

                # 时间
                time_elem = reply_elem.find('span', class_='pubdate')
                reply_time = time_elem.get_text(strip=True) if time_elem else ""

                # 图片
                reply_images = []
                img_elems = reply_elem.find_all('img')
                for img in img_elems:
                    src = img.get('src', '')
                    if src and 'icon' not in src:
                        reply_images.append(src)

                reply = {
                    'reply_index': idx + 1,
                    'author': reply_author,
                    'content': reply_content,
                    'time': reply_time,
                    'images': reply_images,
                    'discussion_id': discussion['discussion_id']
                }

                replies.append(reply)

            except Exception as e:
                print(f"  ⚠️  解析回复 {idx+1} 失败: {e}")
                continue

        discussion['replies'] = replies
        discussion['actual_reply_count'] = len(replies)
        print(f"  ✅ 爬取到 {len(replies)} 条回复")

        time.sleep(SLEEP_SECONDS)
        return discussion

    def crawl(self):
        """主爬取流程"""
        try:
            # 1. 获取讨论列表
            discussion_list = self.get_discussion_list()

            if not discussion_list:
                print("❌ 没有爬取到讨论")
                return

            # 2. 爬取每个讨论详情
            print(f"\n🔍 开始爬取 {len(discussion_list)} 个讨论的详细内容...")

            for idx, discussion in enumerate(discussion_list, 1):
                print(f"\n{'='*70}")
                print(f"进度: [{idx}/{len(discussion_list)}]")

                detailed = self.get_discussion_detail(discussion)
                self.discussions.append(detailed)

                if 'replies' in detailed:
                    self.all_replies.extend(detailed['replies'])

            # 3. 保存数据
            self.save_data()

            print(f"\n{'='*70}")
            print("🎉 爬取完成！")
            print(f"✅ 讨论数: {len(self.discussions)}")
            print(f"✅ 回复数: {len(self.all_replies)}")
            print(f"📁 数据保存在: {DATA_DIR}")
            print(f"{'='*70}")

        except KeyboardInterrupt:
            print("\n\n⚠️  用户中断")
        except Exception as e:
            print(f"❌ 爬取出错: {e}")
            import traceback
            traceback.print_exc()

    def save_data(self):
        """保存数据"""
        timestamp = datetime.now().strftime("%Y-%m-%d")

        # 保存讨论
        disc_file = DATA_DIR / f"{MOVIE_NAME}_讨论_{timestamp}.json"
        with open(disc_file, 'w', encoding='utf-8') as f:
            json.dump(self.discussions, f, ensure_ascii=False, indent=2)
        print(f"\n💾 讨论数据已保存: {disc_file}")

        # 保存回复
        reply_file = DATA_DIR / f"{MOVIE_NAME}_回复_{timestamp}.json"
        with open(reply_file, 'w', encoding='utf-8') as f:
            json.dump(self.all_replies, f, ensure_ascii=False, indent=2)
        print(f"💾 回复数据已保存: {reply_file}")

        # 统计
        stats = {
            'movie': MOVIE_NAME,
            'crawled_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'total_discussions': len(self.discussions),
            'total_replies': len(self.all_replies),
            'avg_replies': round(len(self.all_replies) / len(self.discussions), 2) if self.discussions else 0
        }

        stats_file = DATA_DIR / f"{MOVIE_NAME}_统计_{timestamp}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        print(f"💾 统计信息已保存: {stats_file}")

# ==================== 主程序 ====================

def main():
    print("="*70)
    print("🎬 豆瓣电影讨论爬虫 - 手动版（最简单！）")
    print("="*70)
    print(f"📅 爬取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 目标电影: {MOVIE_NAME}")
    print(f"📊 爬取限制: {MAX_DISCUSSIONS} 个讨论，每个 {MAX_REPLIES} 条回复")
    print("="*70)

    if not COOKIES.strip():
        print("\n💡 提示：当前未设置 Cookie（没关系，大部分内容不需要登录）")
        print("   如果遇到访问限制，再按提示添加 Cookie 即可\n")

    crawler = ManualDoubanCrawler()
    crawler.crawl()

if __name__ == "__main__":
    main()
