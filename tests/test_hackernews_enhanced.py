"""
测试完善后的Hacker News功能
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径 - 现在从tests目录向上一级
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.hackernews_service import HackerNewsService
from src.services.hackernews_report_service import HackerNewsReportService
from src.services.hackernews_update_service import HackerNewsUpdateService
from src.services.llm_service import LLMService
from src.services.notification_service import NotificationService
from src.config.settings import Settings
from datetime import datetime, timezone


async def test_enhanced_features():
    """测试增强后的Hacker News功能"""
    print("🚀 测试完善后的Hacker News功能...")
    print("=" * 60)

    # 测试1: 验证URL配置
    print("🔧 测试1: 验证Hacker News URL配置")
    async with HackerNewsService() as hn_service:
        print(f"✅ Base URL: {hn_service.base_url}")
        print(f"✅ API URL: {hn_service.api_url}")
        assert hn_service.base_url == "https://news.ycombinator.com"

    # 测试2: 测试时间范围数据获取
    print("\n📊 测试2: 测试时间范围数据获取")
    async with HackerNewsService() as hn_service:
        # 测试不同时间范围
        for hours in [1, 6, 24]:
            stories = await hn_service.get_current_hot_topics(hours=hours)
            print(f"✅ 过去{hours}小时: 获取到{len(stories)}个话题")

    # 测试3: 测试prompt模板加载
    print("\n📝 测试3: 测试prompt模板加载")
    try:
        settings = Settings.from_config_file()
        llm_service = LLMService()
        report_service = HackerNewsReportService(llm_service)

        # 验证模板是否正确加载
        template_content = report_service.prompt_template
        assert "Hacker News" in template_content
        assert "技术专家" in template_content
        print("✅ prompt模板加载成功")
        print(f"📄 模板长度: {len(template_content)} 字符")
    except Exception as e:
        print(f"❌ prompt模板测试失败: {str(e)}")

    # 测试4: 测试简化的更新服务
    print("\n🔄 测试4: 测试简化的更新服务")
    try:
        notification_service = NotificationService(settings)
        update_service = HackerNewsUpdateService(
            notification_service,
            report_service
        )

        # 测试获取最新话题
        latest_stories = await update_service.get_latest_stories(limit=5)
        print(f"✅ 获取最新话题: {len(latest_stories)}个")

        # 测试获取时间范围话题
        range_stories = await update_service.get_stories_in_range(hours=12)
        print(f"✅ 获取12小时内话题: {len(range_stories)}个")

        # 测试服务状态
        status = update_service.get_status()
        print(f"✅ 服务状态: {status['status']}")

    except Exception as e:
        print(f"❌ 更新服务测试失败: {str(e)}")

    # 测试5: 测试报告生成（使用真实数据）
    print("\n📋 测试5: 测试报告生成")
    try:
        # 生成小时报告
        async with HackerNewsService() as hn_service:
            stories = await hn_service.get_current_hot_topics(hours=24)

            if stories:
                report = await report_service.generate_hourly_report(
                    stories, datetime.now(timezone.utc), hours=24
                )

                print(f"✅ 报告生成成功，长度: {len(report)} 字符")

                # 验证报告格式
                if "# Hacker News 热门话题" in report:
                    print("✅ 报告格式正确")
                else:
                    print("⚠️  使用备用报告格式")

                # 显示报告预览
                preview = report[:300] + "..." if len(report) > 300 else report
                print(f"\n📖 报告预览:\n{preview}")
            else:
                print("⚠️  未获取到话题数据，跳过报告生成测试")

    except Exception as e:
        print(f"❌ 报告生成测试失败: {str(e)}")

    print("\n" + "=" * 60)
    print("🎉 Hacker News功能测试完成!")


async def demo_usage():
    """演示使用方法"""
    print("\n" + "=" * 60)
    print("💡 使用方法演示:")
    print("=" * 60)

    print("1. 直接运行主程序 (后台监控):")
    print("   python -m src.main")

    print("\n2. 启动Web界面:")
    print("   python -m src.main --web")

    print("\n3. 使用专用CLI工具:")
    print("   python hackernews_cli.py latest --limit 10")
    print("   python hackernews_cli.py report --hours 12")
    print("   python hackernews_cli.py summary")
    print("   python hackernews_cli.py status")

    print("\n4. 功能特点:")
    print("   ✅ 自动每小时扫描热门话题")
    print("   ✅ 使用您的prompt模板生成中文分析报告")
    print("   ✅ 支持任意时间范围数据获取")
    print("   ✅ 无需订阅管理，单一数据源")
    print("   ✅ 自动保存报告到daily_progress目录")


if __name__ == "__main__":
    asyncio.run(test_enhanced_features())
    asyncio.run(demo_usage())
