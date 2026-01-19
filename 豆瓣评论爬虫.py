#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
豆瓣电影评论爬虫 - 爬取短评和长评
适用于电影研究项目，采集观众评论数据

使用方法：
1. pip install requests beautifulsoup4 lxml
2. 配置电影ID和Cookie（可选）
3. python3 豆瓣评论爬虫.py
"""

import requests
import json
import time
import re
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup

# ==================== 配置区域 ====================

# Cookie（可选！大部分评论不需要登录）
# 如果爬取失败，添加Cookie：浏览器登录豆瓣 -> F12 -> Network -> 刷新 -> Headers -> Cookie
COOKIES = """
"""

# 电影配置（修改这里）
MOVIES = [
    {"id": "36035676", "name": "流浪地球2"},
    # {"id": "35725869", "name": "消失的她"},
    # {"id": "35943560", "name": "长安三万里"},
    # {"id": "35766477", "name": "封神第一部"},
    # {"id": "35749412", "name": "孤注一掷"},
]

# 爬取控制
MAX_SHORT_REVIEWS = 500   # 最多爬取多少条短评（每页20条）
MAX_LONG_REVIEWS = 100    # 最多爬取多少条长评（每页20条）
SLEEP_SECONDS = 2         # 请求间隔（秒）

# 数据保存目录
DATA_DIR = Path("data/douban/reviews")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ==================== 爬虫类 ====================

class DoubanReviewCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.setup_session()
        self.short_reviews = []
        self.long_reviews = []

    def setup_session(self):
        """设置请求头和Cookie"""
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
            'Referer': 'https://movie.douban.com/',
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
            print(f"  ❌ 请求失败: {e}")
            return None

    def get_short_reviews(self, movie_id, movie_name):
        """
        爬取短评
        URL格式：https://movie.douban.com/subject/{id}/comments?start={start}&limit=20&status=P&sort=new_score
        """
        print(f"\n📝 开始爬取【{movie_name}】的短评...")

        reviews = []
        page = 0

        while len(reviews) < MAX_SHORT_REVIEWS:
            start = page * 20
            url = f"https://movie.douban.com/subject/{movie_id}/comments?start={start}&limit=20&status=P&sort=new_score"

            print(f"\n  📄 第 {page + 1} 页（已爬 {len(reviews)} 条）")

            html = self.get_page(url)
            if not html:
                break

            # 检查是否需要登录
            if '登录豆瓣' in html or 'login.douban.com' in html:
                print("\n  ⚠️  需要登录！请添加 Cookie")
                break

            soup = BeautifulSoup(html, 'lxml')

            # 查找评论列表
            comment_items = soup.find_all('div', class_='comment-item')

            if not comment_items:
                print("  📌 没有更多短评了")
                break

            for item in comment_items:
                try:
                    # 评论ID
                    comment_id = item.get('data-cid', '')

                    # 用户信息
                    user_elem = item.find('span', class_='comment-info')
                    user_link = user_elem.find('a') if user_elem else None
                    username = user_link.get_text(strip=True) if user_link else "匿名"
                    user_url = user_link['href'] if user_link and user_link.has_attr('href') else ""

                    # 评分（星级）
                    rating_elem = item.find('span', class_='rating')
                    rating_text = ""
                    rating_value = 0
                    if rating_elem:
                        rating_class = rating_elem.get('class', [])
                        for cls in rating_class:
                            if 'allstar' in cls:
                                # allstar50 -> 5星，allstar40 -> 4星
                                match = re.search(r'allstar(\d+)', cls)
                                if match:
                                    rating_value = int(match.group(1)) / 10
                                    rating_text = f"{rating_value}星"
                                break

                    # 评论内容
                    content_elem = item.find('span', class_='short')
                    content = content_elem.get_text(strip=True) if content_elem else ""

                    # 点赞数
                    vote_elem = item.find('span', class_='votes')
                    votes = int(vote_elem.get_text(strip=True)) if vote_elem and vote_elem.get_text(strip=True).isdigit() else 0

                    # 评论时间
                    time_elem = item.find('span', class_='comment-time')
                    comment_time = time_elem.get_text(strip=True) if time_elem else ""

                    # IP位置
                    location_elem = item.find('span', class_='comment-location')
                    location = location_elem.get_text(strip=True) if location_elem else ""

                    review = {
                        'comment_id': comment_id,
                        'type': '短评',
                        'movie_id': movie_id,
                        'movie_name': movie_name,
                        'username': username,
                        'user_url': user_url,
                        'rating': rating_value,
                        'rating_text': rating_text,
                        'content': content,
                        'votes': votes,
                        'time': comment_time,
                        'location': location,
                        'crawled_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }

                    reviews.append(review)
                    print(f"    ✅ [{len(reviews)}] {username}: {content[:50]}...")

                    if len(reviews) >= MAX_SHORT_REVIEWS:
                        break

                except Exception as e:
                    print(f"    ⚠️  解析短评失败: {e}")
                    continue

            if len(reviews) >= MAX_SHORT_REVIEWS:
                break

            # 检查是否还有下一页
            if len(comment_items) < 20:
                print("  📌 已到最后一页")
                break

            page += 1
            time.sleep(SLEEP_SECONDS)

        print(f"\n  ✅ 共爬取 {len(reviews)} 条短评")
        return reviews

    def get_long_reviews(self, movie_id, movie_name):
        """
        爬取长评（影评）
        URL格式：https://movie.douban.com/subject/{id}/reviews?start={start}
        """
        print(f"\n📝 开始爬取【{movie_name}】的长评...")

        reviews = []
        page = 0

        while len(reviews) < MAX_LONG_REVIEWS:
            start = page * 20
            url = f"https://movie.douban.com/subject/{movie_id}/reviews?start={start}"

            print(f"\n  📄 第 {page + 1} 页（已爬 {len(reviews)} 条）")

            html = self.get_page(url)
            if not html:
                break

            # 检查登录
            if '登录豆瓣' in html or 'login.douban.com' in html:
                print("\n  ⚠️  需要登录！请添加 Cookie")
                break

            soup = BeautifulSoup(html, 'lxml')

            # 查找影评列表
            review_items = soup.find_all('div', class_='review-item')

            if not review_items:
                print("  📌 没有更多长评了")
                break

            for item in review_items:
                try:
                    # 影评ID
                    review_id = item.get('data-cid', '')

                    # 标题
                    title_elem = item.find('h2')
                    title_link = title_elem.find('a') if title_elem else None
                    title = title_link.get_text(strip=True) if title_link else ""
                    review_url = title_link['href'] if title_link and title_link.has_attr('href') else ""

                    # 用户信息
                    user_elem = item.find('a', class_='name')
                    username = user_elem.get_text(strip=True) if user_elem else "匿名"
                    user_url = user_elem['href'] if user_elem and user_elem.has_attr('href') else ""

                    # 评分
                    rating_elem = item.find('span', class_='rating')
                    rating_value = 0
                    if rating_elem:
                        rating_class = rating_elem.get('class', [])
                        for cls in rating_class:
                            if 'allstar' in cls:
                                match = re.search(r'allstar(\d+)', cls)
                                if match:
                                    rating_value = int(match.group(1)) / 10
                                break

                    # 影评摘要
                    summary_elem = item.find('div', class_='short-content')
                    summary = summary_elem.get_text(strip=True) if summary_elem else ""

                    # 有用数
                    useful_elem = item.find('span', class_='vote-count')
                    useful_count = int(useful_elem.get_text(strip=True)) if useful_elem and useful_elem.get_text(strip=True).isdigit() else 0

                    # 发布时间
                    time_elem = item.find('span', class_='main-meta')
                    publish_time = time_elem.get_text(strip=True) if time_elem else ""

                    review = {
                        'review_id': review_id,
                        'type': '长评',
                        'movie_id': movie_id,
                        'movie_name': movie_name,
                        'title': title,
                        'url': review_url,
                        'username': username,
                        'user_url': user_url,
                        'rating': rating_value,
                        'summary': summary,
                        'useful_count': useful_count,
                        'time': publish_time,
                        'crawled_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }

                    reviews.append(review)
                    print(f"    ✅ [{len(reviews)}] {username}: {title[:50]}...")

                    if len(reviews) >= MAX_LONG_REVIEWS:
                        break

                except Exception as e:
                    print(f"    ⚠️  解析长评失败: {e}")
                    continue

            if len(reviews) >= MAX_LONG_REVIEWS:
                break

            if len(review_items) < 20:
                print("  📌 已到最后一页")
                break

            page += 1
            time.sleep(SLEEP_SECONDS)

        print(f"\n  ✅ 共爬取 {len(reviews)} 条长评")
        return reviews

    def crawl_movie(self, movie):
        """爬取单部电影的评论"""
        movie_id = movie['id']
        movie_name = movie['name']

        print(f"\n{'='*70}")
        print(f"🎬 开始爬取电影：{movie_name} (ID: {movie_id})")
        print(f"{'='*70}")

        # 爬取短评
        short_reviews = self.get_short_reviews(movie_id, movie_name)
        self.short_reviews.extend(short_reviews)

        # 爬取长评
        long_reviews = self.get_long_reviews(movie_id, movie_name)
        self.long_reviews.extend(long_reviews)

        # 保存当前电影的数据
        self.save_movie_data(movie)

        print(f"\n{'='*70}")
        print(f"✅ 【{movie_name}】爬取完成！")
        print(f"   短评: {len(short_reviews)} 条")
        print(f"   长评: {len(long_reviews)} 条")
        print(f"{'='*70}")

    def save_movie_data(self, movie):
        """保存单部电影的数据"""
        timestamp = datetime.now().strftime("%Y-%m-%d")
        movie_name = movie['name']

        # 筛选当前电影的评论
        movie_short = [r for r in self.short_reviews if r['movie_name'] == movie_name]
        movie_long = [r for r in self.long_reviews if r['movie_name'] == movie_name]

        # 保存短评
        if movie_short:
            short_file = DATA_DIR / f"{movie_name}_短评_{timestamp}.json"
            with open(short_file, 'w', encoding='utf-8') as f:
                json.dump(movie_short, f, ensure_ascii=False, indent=2)
            print(f"\n  💾 短评已保存: {short_file}")

        # 保存长评
        if movie_long:
            long_file = DATA_DIR / f"{movie_name}_长评_{timestamp}.json"
            with open(long_file, 'w', encoding='utf-8') as f:
                json.dump(movie_long, f, ensure_ascii=False, indent=2)
            print(f"  💾 长评已保存: {long_file}")

    def save_all_data(self):
        """保存所有数据"""
        timestamp = datetime.now().strftime("%Y-%m-%d")

        # 保存所有短评
        if self.short_reviews:
            all_short_file = DATA_DIR / f"所有电影_短评_{timestamp}.json"
            with open(all_short_file, 'w', encoding='utf-8') as f:
                json.dump(self.short_reviews, f, ensure_ascii=False, indent=2)
            print(f"\n💾 所有短评已保存: {all_short_file}")

        # 保存所有长评
        if self.long_reviews:
            all_long_file = DATA_DIR / f"所有电影_长评_{timestamp}.json"
            with open(all_long_file, 'w', encoding='utf-8') as f:
                json.dump(self.long_reviews, f, ensure_ascii=False, indent=2)
            print(f"💾 所有长评已保存: {all_long_file}")

        # 统计信息
        stats = {
            'crawled_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'total_movies': len(MOVIES),
            'total_short_reviews': len(self.short_reviews),
            'total_long_reviews': len(self.long_reviews),
            'total_reviews': len(self.short_reviews) + len(self.long_reviews),
            'movies': [
                {
                    'name': m['name'],
                    'short_count': len([r for r in self.short_reviews if r['movie_name'] == m['name']]),
                    'long_count': len([r for r in self.long_reviews if r['movie_name'] == m['name']]),
                }
                for m in MOVIES
            ]
        }

        stats_file = DATA_DIR / f"爬取统计_{timestamp}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        print(f"💾 统计信息已保存: {stats_file}")

    def crawl(self):
        """主爬取流程"""
        print("="*70)
        print("🎬 豆瓣电影评论爬虫")
        print("="*70)
        print(f"📅 爬取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 目标电影: {len(MOVIES)} 部")
        print(f"📊 短评限制: {MAX_SHORT_REVIEWS} 条/部")
        print(f"📊 长评限制: {MAX_LONG_REVIEWS} 条/部")
        print("="*70)

        if not COOKIES.strip():
            print("\n💡 提示：当前未设置 Cookie（大部分评论不需要登录）")
            print("   如果遇到限制，再添加 Cookie 即可\n")

        try:
            for idx, movie in enumerate(MOVIES, 1):
                self.crawl_movie(movie)

                if idx < len(MOVIES):
                    wait_time = 5
                    print(f"\n⏳ 等待 {wait_time} 秒后继续下一部电影...")
                    time.sleep(wait_time)

            # 保存汇总数据
            self.save_all_data()

            print("\n" + "="*70)
            print("🎉 所有电影爬取完成！")
            print("="*70)
            print(f"✅ 总短评: {len(self.short_reviews)} 条")
            print(f"✅ 总长评: {len(self.long_reviews)} 条")
            print(f"📁 数据保存在: {DATA_DIR}")
            print("="*70)

        except KeyboardInterrupt:
            print("\n\n⚠️  用户中断")
            self.save_all_data()
        except Exception as e:
            print(f"\n❌ 爬取出错: {e}")
            import traceback
            traceback.print_exc()
            self.save_all_data()

# ==================== 主程序 ====================

def main():
    crawler = DoubanReviewCrawler()
    crawler.crawl()

if __name__ == "__main__":
    main()
