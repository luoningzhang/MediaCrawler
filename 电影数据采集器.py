#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电影观众传播影响力研究 - 数据采集工具
针对五部中国电影的社交媒体数据批量采集
研究对象：《流浪地球2》《消失的她》《长安三万里》《封神第一部》《孤注一掷》
"""

import subprocess
import sys
import time
from datetime import datetime

# ==================== 配置区域 ====================

# 五部电影列表
MOVIES = [
    "流浪地球2",
    "消失的她",
    "长安三万里",
    "封神第一部",
    "孤注一掷"
]

# 平台列表（按需选择）
PLATFORMS = [
    {"code": "xhs", "name": "小红书"},
    {"code": "dy", "name": "抖音"},
    {"code": "wb", "name": "微博"}
]

# 爬取配置
CRAWLER_CONFIG = {
    "login_type": "qrcode",  # 登录方式：qrcode | phone | cookie
    "crawler_type": "search",  # 爬取类型：search | detail | creator
}

# ==================== 工具函数 ====================

def print_banner():
    """打印欢迎横幅"""
    print("=" * 70)
    print("🎬 电影观众传播影响力研究 - 数据采集工具")
    print("=" * 70)
    print(f"📅 采集时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 研究对象: {len(MOVIES)} 部电影")
    print(f"📱 采集平台: {', '.join([p['name'] for p in PLATFORMS])}")
    print("=" * 70)
    print()

def print_step(step, total, movie, platform):
    """打印当前步骤"""
    print("\n" + "=" * 70)
    print(f"📊 进度: [{step}/{total}]")
    print(f"🎬 当前电影: {movie}")
    print(f"📱 当前平台: {platform['name']} ({platform['code']})")
    print("=" * 70)

def run_crawler(platform_code, keyword):
    """
    运行爬虫命令

    Args:
        platform_code: 平台代码 (xhs/dy/wb)
        keyword: 搜索关键词（电影名）
    """
    cmd = [
        sys.executable,  # Python 解释器路径
        "main.py",
        "--platform", platform_code,
        "--lt", CRAWLER_CONFIG["login_type"],
        "--type", CRAWLER_CONFIG["crawler_type"],
        "--keywords", keyword
    ]

    print(f"\n🚀 执行命令: {' '.join(cmd)}\n")

    try:
        # 运行爬虫（实时输出）
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )

        # 实时打印输出
        for line in process.stdout:
            print(line, end='')

        # 等待进程结束
        return_code = process.wait()

        if return_code == 0:
            print(f"\n✅ 采集成功！")
            return True
        else:
            print(f"\n❌ 采集失败，返回码: {return_code}")
            return False

    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断采集")
        process.terminate()
        return False
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        return False

def ask_user_choice(question, options):
    """
    询问用户选择

    Args:
        question: 问题
        options: 选项列表

    Returns:
        用户选择的选项索引列表
    """
    print(f"\n{question}")
    for i, option in enumerate(options, 1):
        print(f"  {i}. {option}")
    print(f"  0. 全部")

    while True:
        choice = input("\n请输入选项编号（多个用逗号分隔，如: 1,3,5）: ").strip()

        if choice == "0":
            return list(range(len(options)))

        try:
            indices = [int(x.strip()) - 1 for x in choice.split(",")]
            if all(0 <= i < len(options) for i in indices):
                return indices
            else:
                print("❌ 输入有误，请重新输入！")
        except:
            print("❌ 格式错误，请输入数字编号！")

# ==================== 主程序 ====================

def main():
    """主函数"""
    print_banner()

    # 1. 选择要采集的电影
    print("📋 第一步：选择要采集的电影")
    movie_indices = ask_user_choice("请选择要采集的电影:", MOVIES)
    selected_movies = [MOVIES[i] for i in movie_indices]

    # 2. 选择要采集的平台
    print("\n📋 第二步：选择要采集的平台")
    platform_names = [f"{p['name']} ({p['code']})" for p in PLATFORMS]
    platform_indices = ask_user_choice("请选择要采集的平台:", platform_names)
    selected_platforms = [PLATFORMS[i] for i in platform_indices]

    # 3. 确认配置
    print("\n" + "=" * 70)
    print("📝 采集配置确认")
    print("=" * 70)
    print(f"🎬 电影列表: {', '.join(selected_movies)}")
    print(f"📱 平台列表: {', '.join([p['name'] for p in selected_platforms])}")
    print(f"📊 总任务数: {len(selected_movies)} × {len(selected_platforms)} = {len(selected_movies) * len(selected_platforms)} 个")
    print("=" * 70)

    confirm = input("\n确认开始采集吗？(y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ 已取消采集")
        return

    # 4. 开始批量采集
    total_tasks = len(selected_movies) * len(selected_platforms)
    current_task = 0
    success_count = 0
    fail_count = 0

    start_time = time.time()

    for movie in selected_movies:
        for platform in selected_platforms:
            current_task += 1

            # 打印当前步骤
            print_step(current_task, total_tasks, movie, platform)

            # 首次运行需要登录提示
            if current_task == 1:
                print("\n⚠️  首次运行需要扫码登录，请准备好手机！")
                input("按回车键继续...")

            # 运行爬虫
            success = run_crawler(platform["code"], movie)

            if success:
                success_count += 1
            else:
                fail_count += 1
                retry = input("\n是否重试当前任务？(y/n): ").strip().lower()
                if retry == 'y':
                    success = run_crawler(platform["code"], movie)
                    if success:
                        success_count += 1
                        fail_count -= 1

            # 任务间隔（避免被封）
            if current_task < total_tasks:
                wait_time = 5
                print(f"\n⏳ 等待 {wait_time} 秒后进行下一个任务...")
                time.sleep(wait_time)

    # 5. 采集完成总结
    elapsed_time = time.time() - start_time

    print("\n" + "=" * 70)
    print("🎉 采集任务全部完成！")
    print("=" * 70)
    print(f"✅ 成功: {success_count} 个任务")
    print(f"❌ 失败: {fail_count} 个任务")
    print(f"⏱️  总耗时: {elapsed_time/60:.1f} 分钟")
    print(f"📁 数据保存位置: ./data/ 目录")
    print("=" * 70)

    # 6. 数据文件说明
    print("\n📄 生成的数据文件说明:")
    print("-" * 70)
    for platform in selected_platforms:
        print(f"\n{platform['name']}:")
        print(f"  - {platform['code']}_notes.json (笔记/视频数据)")
        print(f"  - {platform['code']}_comments.json (评论数据)")
        if platform['code'] == 'xhs':
            print(f"  - {platform['code']}_creators.json (创作者数据)")
    print("-" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  程序已被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
