#!/usr/bin/env python3
"""
快速测试脚本 - 立即运行一次采集和发送
"""

import sys
import os

# 确保在正确的目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import collect_and_send

if __name__ == "__main__":
    print("=" * 70)
    print("🚴 自行车品牌日报收集器 - 快速测试")
    print("=" * 70)
    print()
    print("📧 测试配置：")
    print("   - 发件人：2645583917@qq.com")
    print("   - 收件人：2645583917@qq.com")
    print("   - 监控品牌：12个国际自行车品牌")
    print()
    print("⏳ 正在执行采集和发送...")
    print("-" * 70)
    print()
    
    try:
        collect_and_send()
        print()
        print("-" * 70)
        print("✅ 测试完成！")
        print()
        print("📧 请检查你的QQ邮箱：2645583917@qq.com")
        print("   如果5分钟内没有收到邮件，请查看 logs/app.log 了解详情")
        print()
        print("=" * 70)
    except Exception as e:
        print()
        print("-" * 70)
        print(f"❌ 测试失败：{str(e)}")
        print()
        print("📋 请检查 logs/app.log 了解详细错误信息")
        print("=" * 70)
        sys.exit(1)
