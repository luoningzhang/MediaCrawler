#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
豆瓣反爬虫绕过工具
使用 Selenium 模拟真实浏览器访问，自动处理 JavaScript 验证
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import json
from datetime import datetime
from pathlib import Path

# 配置
DOUBAN_URL = "https://movie.douban.com/subject/36035676/discussion/"
MOVIE_NAME = "流浪地球2"
MAX_DISCUSSIONS = 20  # 测试用，先爬 20 个
MAX_REPLIES = 50

# 数据保存目录
DATA_DIR = Path("data/douban/json")
DATA_DIR.mkdir(parents=True, exist_ok=True)

print("="*70)
print("🎬 豆瓣电影讨论爬虫 - Selenium 版（绕过反爬虫）")
print("="*70)
print(f"🎯 目标: {MOVIE_NAME}")
print(f"📊 限制: {MAX_DISCUSSIONS} 个讨论")
print("="*70)

# 初始化浏览器
print("\n🚀 正在启动 Chrome 浏览器...")
options = webdriver.ChromeOptions()
# options.add_argument('--headless')  # 取消注释可后台运行
options.add_argument('--disable-blink-features=AutomationControlled')

try:
    driver = webdriver.Chrome(options=options)
    print("✅ 浏览器启动成功！\n")
except Exception as e:
    print(f"❌ 启动浏览器失败: {e}")
    print("\n请确保已安装 ChromeDriver:")
    print("  Mac: brew install chromedriver")
    print("  或访问: https://chromedriver.chromium.org/")
    exit(1)

try:
    # 访问页面
    print(f"🔍 正在访问: {DOUBAN_URL}")
    driver.get(DOUBAN_URL)

    # 等待页面加载（等待反爬虫验证完成）
    print("⏳ 等待页面加载（自动处理反爬虫验证）...")
    time.sleep(5)  # 给足够时间让 JavaScript 执行

    # 检查是否成功加载
    soup = BeautifulSoup(driver.page_source, 'lxml')

    # 保存 HTML 用于调试
    with open('douban_selenium_debug.html', 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print("💾 页面内容已保存到: douban_selenium_debug.html\n")

    # 查找讨论列表
    print("🔍 查找讨论列表...")

    # 尝试多种选择器
    discussions_found = False

    # 方法1：通过 CSS 选择器
    try:
        topics = driver.find_elements(By.CSS_SELECTOR, 'tr.topic')
        if topics:
            print(f"✅ 找到 {len(topics)} 个讨论（使用 tr.topic）\n")
            discussions_found = True

            # 提取前几个讨论信息
            for i, topic in enumerate(topics[:5], 1):
                try:
                    title_elem = topic.find_element(By.CSS_SELECTOR, 'td.title a')
                    title = title_elem.text
                    url = title_elem.get_attribute('href')
                    print(f"{i}. {title}")
                    print(f"   URL: {url}\n")
                except:
                    pass
    except:
        pass

    # 方法2：通过 XPath
    if not discussions_found:
        try:
            topics = driver.find_elements(By.XPATH, "//table[@class='olt']//tr")
            if len(topics) > 0:
                print(f"✅ 找到 {len(topics)} 个元素（使用 XPath）\n")
                discussions_found = True
        except:
            pass

    if not discussions_found:
        print("❌ 未找到讨论列表")
        print("\n可能的原因:")
        print("1. 页面结构变化")
        print("2. 反爬虫验证未通过")
        print("3. 需要登录")
        print("\n请查看 douban_selenium_debug.html 文件")

    # 检查页面内容
    page_text = driver.page_source
    if '载入中' in page_text:
        print("\n⚠️  页面显示'载入中'，可能是反爬虫验证未完成")
    if '登录' in page_text and '登录豆瓣' in page_text:
        print("\n⚠️  页面要求登录")

    print("\n" + "="*70)
    print("💡 提示：请打开 douban_selenium_debug.html 查看实际页面内容")
    print("="*70)

except KeyboardInterrupt:
    print("\n\n⚠️  用户中断")
except Exception as e:
    print(f"\n❌ 发生错误: {e}")
    import traceback
    traceback.print_exc()
finally:
    print("\n🔚 关闭浏览器...")
    driver.quit()
