#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
豆瓣爬虫调试工具 - 查看页面实际内容
帮助诊断为什么爬取失败
"""

import requests
from bs4 import BeautifulSoup

# 测试 URL
url = "https://movie.douban.com/subject/35943560/discussion/?start=0&sort_by=time"

print("🔍 正在访问豆瓣...")
print(f"URL: {url}\n")

# 发送请求
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

try:
    response = requests.get(url, headers=headers, timeout=10)
    response.encoding = 'utf-8'

    print(f"✅ 状态码: {response.status_code}")
    print(f"✅ 内容长度: {len(response.text)} 字符\n")

    # 保存原始 HTML
    with open('douban_debug.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print("💾 完整 HTML 已保存到: douban_debug.html")

    # 检查是否需要登录
    if '登录豆瓣' in response.text or 'login.douban.com' in response.text:
        print("\n⚠️  页面提示需要登录！")

    # 检查是否有验证码
    if '验证' in response.text or 'captcha' in response.text.lower():
        print("\n⚠️  页面要求验证码！")

    # 解析讨论
    soup = BeautifulSoup(response.text, 'lxml')

    # 尝试多种选择器
    print("\n" + "="*70)
    print("🔍 测试不同的选择器：")
    print("="*70)

    # 选择器 1
    topics1 = soup.find_all('tr', class_='topic')
    print(f"\n1. 'tr.topic' 找到: {len(topics1)} 个")

    # 选择器 2
    topics2 = soup.find_all('table', class_='olt')
    print(f"2. 'table.olt' 找到: {len(topics2)} 个")

    # 选择器 3
    topics3 = soup.find_all('div', class_='topic-item')
    print(f"3. 'div.topic-item' 找到: {len(topics3)} 个")

    # 查找所有的 table
    all_tables = soup.find_all('table')
    print(f"4. 所有 table 标签: {len(all_tables)} 个")

    # 查看页面标题
    title = soup.find('title')
    print(f"\n📄 页面标题: {title.get_text() if title else '未找到'}")

    # 查找讨论相关的关键词
    if '讨论' in response.text:
        print("✅ 页面包含'讨论'关键词")

    # 尝试找到第一个讨论的标题
    print("\n" + "="*70)
    print("🔍 尝试提取讨论内容：")
    print("="*70)

    # 方法1：通过 table.olt
    olt_table = soup.find('table', class_='olt')
    if olt_table:
        print("\n✅ 找到 table.olt")
        rows = olt_table.find_all('tr')
        print(f"   包含 {len(rows)} 行")

        for i, row in enumerate(rows[:3]):  # 只看前3行
            print(f"\n   行 {i+1}:")
            print(f"   - class: {row.get('class', [])}")
            title_td = row.find('td', class_='title')
            if title_td:
                link = title_td.find('a')
                if link:
                    print(f"   - 标题: {link.get_text(strip=True)}")
    else:
        print("\n❌ 未找到 table.olt")

        # 显示页面主要内容的结构
        content = soup.find('div', id='content')
        if content:
            print("\n找到主内容区，子元素：")
            for child in content.find_all(recursive=False)[:5]:
                print(f"   - {child.name}: class={child.get('class', [])}")

    print("\n" + "="*70)
    print("💡 提示：")
    print("   1. 请打开 douban_debug.html 文件，查看完整页面内容")
    print("   2. 在浏览器中打开该 URL，对比页面结构")
    print("   3. 检查是否需要登录或验证码")
    print("="*70)

except Exception as e:
    print(f"❌ 请求失败: {e}")
    import traceback
    traceback.print_exc()
