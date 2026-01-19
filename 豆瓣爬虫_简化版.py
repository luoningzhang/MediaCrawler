#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
豆瓣电影讨论爬虫 - 简化版（使用 Selenium）
无需复杂配置，只需要安装 Chrome 浏览器即可

安装依赖：
pip install selenium beautifulsoup4 lxml
"""

import json
import time
import re
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutError, NoSuchElementException
from bs4 import BeautifulSoup

# ==================== 配置区域 ====================

# 豆瓣电影讨论URL
DOUBAN_DISCUSSION_URL = "https://movie.douban.com/subject/36035676/discussion/?start=0&sort_by=time"

# 电影名称（用于保存文件）
MOVIE_NAME = "流浪地球2"

# 爬取控制
MAX_DISCUSSIONS = 50  # 最多爬取多少个讨论（设为 999999 可爬全部）
MAX_REPLIES = 100     # 每个讨论最多爬取多少条回复（设为 999999 可爬全部）
SLEEP_SECONDS = 2     # 请求间隔（秒）

# 数据保存目录
DATA_DIR = Path("data/douban/json")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ==================== 爬虫类 ====================

class SimpleDoubanCrawler:
    def __init__(self):
        self.driver = None
        self.discussions = []
        self.all_replies = []

    def init_driver(self):
        """初始化 Selenium WebDriver"""
        print("🚀 正在启动 Chrome 浏览器...")

        options = webdriver.ChromeOptions()
        # options.add_argument('--headless')  # 如果想后台运行，取消这行注释
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')

        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.implicitly_wait(10)
            print("✅ 浏览器启动成功！")
        except Exception as e:
            print(f"❌ 启动浏览器失败: {e}")
            print("\n请确保已安装 ChromeDriver:")
            print("  方法1: brew install chromedriver (Mac)")
            print("  方法2: 访问 https://chromedriver.chromium.org/ 下载")
            raise

    def login_if_needed(self):
        """检查是否需要登录"""
        if "登录" in self.driver.page_source or "login" in self.driver.current_url.lower():
            print("\n⚠️  需要登录豆瓣账号！")
            print("请在浏览器中手动登录...")
            input("登录完成后，按回车键继续...")
            self.driver.get(DOUBAN_DISCUSSION_URL)
            time.sleep(2)

    def get_discussion_list(self):
        """获取讨论列表"""
        print(f"\n📋 开始爬取讨论列表...")

        self.driver.get(DOUBAN_DISCUSSION_URL)
        time.sleep(2)
        self.login_if_needed()

        discussions = []
        page = 1

        while len(discussions) < MAX_DISCUSSIONS:
            print(f"\n📄 正在爬取第 {page} 页...")

            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            topics = soup.find_all('tr', class_='topic')

            if not topics:
                print("⚠️  没有找到讨论，可能已到最后一页")
                break

            for topic in topics:
                try:
                    # 标题和链接
                    title_elem = topic.find('td', class_='title').find('a')
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    url = title_elem['href'] if title_elem else ""

                    # 作者
                    author_elem = topic.find('td', class_='td-author').find('a')
                    author = author_elem.get_text(strip=True) if author_elem else "未知"

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
            try:
                next_link = self.driver.find_element(By.CSS_SELECTOR, 'span.next a')
                next_url = next_link.get_attribute('href')
                if next_url and 'javascript' not in next_url:
                    self.driver.get(next_url)
                    time.sleep(SLEEP_SECONDS)
                    page += 1
                else:
                    break
            except NoSuchElementException:
                print("📌 已到最后一页")
                break

        print(f"\n✅ 共爬取 {len(discussions)} 个讨论")
        return discussions

    def get_discussion_detail(self, discussion):
        """获取讨论详情"""
        url = discussion['url']
        print(f"\n💬 正在爬取: {discussion['title'][:50]}...")

        try:
            self.driver.get(url)
            time.sleep(SLEEP_SECONDS)

            soup = BeautifulSoup(self.driver.page_source, 'lxml')

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
                    author_elem = reply_elem.find('a', class_='j a_author') or reply_elem.find('span', class_='pubdate').find('a')
                    reply_author = author_elem.get_text(strip=True) if author_elem else "未知"

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

            return discussion

        except Exception as e:
            print(f"❌ 爬取失败: {e}")
            return discussion

    def crawl(self):
        """主爬取流程"""
        try:
            self.init_driver()

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
        finally:
            if self.driver:
                self.driver.quit()
                print("\n🔚 浏览器已关闭")

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
    print("🎬 豆瓣电影讨论爬虫 - 简化版")
    print("="*70)
    print(f"📅 爬取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 目标电影: {MOVIE_NAME}")
    print(f"📊 爬取限制: {MAX_DISCUSSIONS} 个讨论，每个 {MAX_REPLIES} 条回复")
    print("="*70)

    crawler = SimpleDoubanCrawler()
    crawler.crawl()

if __name__ == "__main__":
    main()
