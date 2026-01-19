#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
豆瓣电影讨论爬虫 - 独立版本
专为电影研究项目设计，爬取豆瓣电影讨论区的全部内容
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from typing import List, Dict
import time

# ==================== 配置区域 ====================

# 豆瓣电影讨论URL列表
DOUBAN_DISCUSSION_URLS = [
    "https://movie.douban.com/subject/36035676/discussion/?start=0&sort_by=time",  # 流浪地球2
    # 添加更多电影讨论URL...
]

# 爬取控制
MAX_DISCUSSIONS = 100  # 最多爬取多少个讨论
MAX_REPLIES_PER_DISCUSSION = 200  # 每个讨论最多爬取多少条回复
SLEEP_SECONDS = 2  # 请求间隔（秒）

# 数据保存目录
DATA_DIR = Path("data/douban/json")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ==================== 爬虫类 ====================

class DoubanDiscussionCrawler:
    def __init__(self):
        self.discussions = []
        self.replies = []
        self.browser = None
        self.context = None
        self.page = None

    async def init_browser(self):
        """初始化浏览器"""
        print("🚀 正在启动浏览器...")
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,  # 显示浏览器窗口
            args=['--disable-blink-features=AutomationControlled']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        self.page = await self.context.new_page()
        print("✅ 浏览器启动成功！")

    async def get_discussion_list(self, url: str) -> List[Dict]:
        """
        获取讨论列表

        Args:
            url: 讨论页面URL

        Returns:
            讨论列表
        """
        print(f"\n📋 正在爬取讨论列表: {url}")

        try:
            await self.page.goto(url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(2)

            # 检查是否需要登录
            if "登录" in await self.page.content():
                print("\n⚠️  需要登录豆瓣账号！")
                print("请在打开的浏览器窗口中手动登录...")
                input("登录完成后，按回车键继续...")
                await self.page.reload(wait_until='networkidle')

            discussions = []
            page_count = 0

            while len(discussions) < MAX_DISCUSSIONS:
                page_count += 1
                print(f"\n📄 正在爬取第 {page_count} 页...")

                # 等待讨论列表加载
                try:
                    await self.page.wait_for_selector('tr.topic', timeout=10000)
                except PlaywrightTimeoutError:
                    print("⚠️  未找到讨论列表，可能已到最后一页")
                    break

                # 解析讨论列表
                topic_elements = await self.page.query_selector_all('tr.topic')

                if not topic_elements:
                    print("⚠️  当前页没有讨论，停止爬取")
                    break

                for topic_elem in topic_elements:
                    try:
                        # 标题和链接
                        title_elem = await topic_elem.query_selector('td.title a')
                        if not title_elem:
                            continue

                        title = await title_elem.inner_text()
                        discussion_url = await title_elem.get_attribute('href')

                        # 作者
                        author_elem = await topic_elem.query_selector('td a')
                        author = await author_elem.inner_text() if author_elem else "未知"

                        # 回复数
                        reply_elem = await topic_elem.query_selector('td.r-count')
                        reply_count_text = await reply_elem.inner_text() if reply_elem else "0"
                        reply_count = int(reply_count_text) if reply_count_text.isdigit() else 0

                        # 最后回复时间
                        time_elem = await topic_elem.query_selector('td.time')
                        last_reply_time = await time_elem.inner_text() if time_elem else ""

                        discussion_data = {
                            "discussion_id": discussion_url.split('/')[-2] if discussion_url else "",
                            "title": title.strip(),
                            "url": discussion_url,
                            "author": author.strip(),
                            "reply_count": reply_count,
                            "last_reply_time": last_reply_time.strip(),
                            "crawled_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }

                        discussions.append(discussion_data)
                        print(f"  ✅ [{len(discussions)}] {title[:50]}... (回复: {reply_count})")

                        if len(discussions) >= MAX_DISCUSSIONS:
                            break

                    except Exception as e:
                        print(f"  ⚠️  解析讨论失败: {e}")
                        continue

                if len(discussions) >= MAX_DISCUSSIONS:
                    break

                # 查找下一页链接
                next_page = await self.page.query_selector('span.next a')
                if next_page:
                    next_url = await next_page.get_attribute('href')
                    if next_url and not next_url.startswith('javascript'):
                        # 构建完整URL
                        if next_url.startswith('http'):
                            await self.page.goto(next_url, wait_until='networkidle')
                        else:
                            base_url = url.split('?')[0]
                            full_next_url = base_url + next_url if next_url.startswith('?') else base_url + '?' + next_url
                            await self.page.goto(full_next_url, wait_until='networkidle')

                        await asyncio.sleep(SLEEP_SECONDS)
                    else:
                        print("📌 已到最后一页")
                        break
                else:
                    print("📌 已到最后一页")
                    break

            print(f"\n✅ 共爬取 {len(discussions)} 个讨论")
            return discussions

        except Exception as e:
            print(f"❌ 爬取讨论列表失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def get_discussion_detail(self, discussion: Dict) -> Dict:
        """
        获取讨论详情（包括初始帖子和所有回复）

        Args:
            discussion: 讨论基本信息

        Returns:
            完整的讨论数据
        """
        url = discussion['url']
        print(f"\n💬 正在爬取讨论详情: {discussion['title'][:50]}...")

        try:
            await self.page.goto(url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(2)

            # 获取初始帖子内容
            post_content = ""
            post_images = []

            # 内容
            content_elem = await self.page.query_selector('div#link-report .topic-content')
            if content_elem:
                # 获取文本内容
                post_content = await content_elem.inner_text()

                # 获取图片
                img_elements = await content_elem.query_selector_all('img')
                for img_elem in img_elements:
                    img_src = await img_elem.get_attribute('src')
                    if img_src:
                        post_images.append(img_src)

            # 发布时间
            post_time = ""
            time_elem = await self.page.query_selector('span.color-green')
            if time_elem:
                post_time = await time_elem.inner_text()

            discussion['content'] = post_content.strip()
            discussion['images'] = post_images
            discussion['post_time'] = post_time.strip()

            # 获取所有回复
            replies = []

            try:
                # 等待回复列表
                await self.page.wait_for_selector('div#comments', timeout=5000)

                reply_elements = await self.page.query_selector_all('div.reply-item, div.comment-item')

                for idx, reply_elem in enumerate(reply_elements):
                    if idx >= MAX_REPLIES_PER_DISCUSSION:
                        break

                    try:
                        # 回复者
                        author_elem = await reply_elem.query_selector('a.j.a_author')
                        if not author_elem:
                            author_elem = await reply_elem.query_selector('span.pubdate a')
                        reply_author = await author_elem.inner_text() if author_elem else "未知"

                        # 回复内容
                        content_elem = await reply_elem.query_selector('p.reply-content, div.reply-doc p')
                        if not content_elem:
                            content_elem = await reply_elem.query_selector('p')
                        reply_content = await content_elem.inner_text() if content_elem else ""

                        # 回复时间
                        time_elem = await reply_elem.query_selector('span.pubdate, span.comment-info span')
                        reply_time = await time_elem.inner_text() if time_elem else ""

                        # 回复图片
                        reply_images = []
                        img_elements = await reply_elem.query_selector_all('img')
                        for img_elem in img_elements:
                            img_src = await img_elem.get_attribute('src')
                            if img_src and 'icon' not in img_src:  # 过滤掉图标
                                reply_images.append(img_src)

                        reply_data = {
                            "reply_index": idx + 1,
                            "author": reply_author.strip(),
                            "content": reply_content.strip(),
                            "time": reply_time.strip(),
                            "images": reply_images,
                            "discussion_id": discussion['discussion_id']
                        }

                        replies.append(reply_data)

                    except Exception as e:
                        print(f"  ⚠️  解析回复 {idx+1} 失败: {e}")
                        continue

                print(f"  ✅ 爬取到 {len(replies)} 条回复")

            except PlaywrightTimeoutError:
                print(f"  ℹ️  该讨论暂无回复")

            discussion['replies'] = replies
            discussion['actual_reply_count'] = len(replies)

            await asyncio.sleep(SLEEP_SECONDS)

            return discussion

        except Exception as e:
            print(f"❌ 爬取讨论详情失败: {e}")
            import traceback
            traceback.print_exc()
            return discussion

    async def crawl(self, url: str):
        """
        主爬取流程

        Args:
            url: 讨论列表URL
        """
        try:
            await self.init_browser()

            # 1. 获取讨论列表
            discussions = await self.get_discussion_list(url)

            if not discussions:
                print("❌ 没有爬取到讨论列表")
                return

            # 2. 爬取每个讨论的详情
            print(f"\n🔍 开始爬取 {len(discussions)} 个讨论的详细内容...")

            for idx, discussion in enumerate(discussions, 1):
                print(f"\n{'='*70}")
                print(f"进度: [{idx}/{len(discussions)}]")

                detailed_discussion = await self.get_discussion_detail(discussion)
                self.discussions.append(detailed_discussion)

                # 提取所有回复到单独的列表
                if 'replies' in detailed_discussion:
                    self.replies.extend(detailed_discussion['replies'])

            # 3. 保存数据
            self.save_data()

            print(f"\n{'='*70}")
            print("🎉 爬取完成！")
            print(f"✅ 讨论数: {len(self.discussions)}")
            print(f"✅ 回复数: {len(self.replies)}")
            print(f"📁 数据保存在: {DATA_DIR}")
            print(f"{'='*70}")

        except Exception as e:
            print(f"❌ 爬取过程出错: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.browser:
                await self.browser.close()
                print("\n🔚 浏览器已关闭")

    def save_data(self):
        """保存数据到JSON文件"""
        timestamp = datetime.now().strftime("%Y-%m-%d")

        # 保存讨论数据
        discussions_file = DATA_DIR / f"douban_discussions_{timestamp}.json"
        with open(discussions_file, 'w', encoding='utf-8') as f:
            json.dump(self.discussions, f, ensure_ascii=False, indent=2)
        print(f"\n💾 讨论数据已保存: {discussions_file}")

        # 保存回复数据
        replies_file = DATA_DIR / f"douban_replies_{timestamp}.json"
        with open(replies_file, 'w', encoding='utf-8') as f:
            json.dump(self.replies, f, ensure_ascii=False, indent=2)
        print(f"💾 回复数据已保存: {replies_file}")

        # 生成统计信息
        stats = {
            "crawled_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_discussions": len(self.discussions),
            "total_replies": len(self.replies),
            "discussions_with_replies": len([d for d in self.discussions if d.get('actual_reply_count', 0) > 0]),
            "avg_replies_per_discussion": round(len(self.replies) / len(self.discussions), 2) if self.discussions else 0
        }

        stats_file = DATA_DIR / f"douban_stats_{timestamp}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        print(f"💾 统计信息已保存: {stats_file}")

# ==================== 主程序 ====================

async def main():
    """主函数"""
    print("="*70)
    print("🎬 豆瓣电影讨论爬虫")
    print("="*70)
    print(f"📅 爬取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 爬取目标: {len(DOUBAN_DISCUSSION_URLS)} 个电影讨论区")
    print(f"📊 爬取限制: 最多 {MAX_DISCUSSIONS} 个讨论，每个讨论最多 {MAX_REPLIES_PER_DISCUSSION} 条回复")
    print("="*70)

    for idx, url in enumerate(DOUBAN_DISCUSSION_URLS, 1):
        print(f"\n\n{'#'*70}")
        print(f"# 开始爬取第 {idx}/{len(DOUBAN_DISCUSSION_URLS)} 个电影讨论区")
        print(f"# URL: {url}")
        print(f"{'#'*70}")

        crawler = DoubanDiscussionCrawler()
        await crawler.crawl(url)

        if idx < len(DOUBAN_DISCUSSION_URLS):
            wait_time = 10
            print(f"\n⏳ 等待 {wait_time} 秒后继续下一个...")
            await asyncio.sleep(wait_time)

    print("\n\n" + "="*70)
    print("🎉 全部爬取任务完成！")
    print(f"📁 数据保存在: {DATA_DIR}")
    print("="*70)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断程序")
    except Exception as e:
        print(f"\n❌ 程序出错: {e}")
        import traceback
        traceback.print_exc()
