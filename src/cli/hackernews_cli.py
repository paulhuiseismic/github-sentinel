"""
Hacker News CLI 工具 - 简化版
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone
import argparse

# 添加项目根目录到Python路径 - 现在需要向上两级到达项目根目录
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.hackernews_service import HackerNewsService
from src.services.hackernews_report_service import HackerNewsReportService
from src.services.hackernews_update_service import HackerNewsUpdateService
from src.services.llm_service import LLMService
from src.services.notification_service import NotificationService
from src.config.settings import Settings


class HackerNewsCLI:
    """Hacker News 命令行工具"""

    def __init__(self):
        # 初始化服务
        self.settings = Settings.from_config_file()
        self.llm_service = LLMService()
        self.notification_service = NotificationService(self.settings)
        self.report_service = HackerNewsReportService(self.llm_service)
        self.update_service = HackerNewsUpdateService(
            self.notification_service,
            self.report_service
        )

    async def get_latest_stories(self, limit: int = 10):
        """获取最新热门话题"""
        print(f"📰 获取Hacker News最新{limit}个热门话题...")

        try:
            stories = await self.update_service.get_latest_stories(limit)

            if stories:
                print(f"✅ 成功获取{len(stories)}个话题:")
                for i, story in enumerate(stories, 1):
                    print(f"  {i}. {story['title']} (分数: {story['score']})")
                    if story.get('url'):
                        print(f"     {story['url']}")
                    print()
            else:
                print("❌ 未找到热门话题")

        except Exception as e:
            print(f"❌ 获取话题失败: {str(e)}")

    async def generate_report(self, hours: int = 24):
        """生成指定时间范围的报告"""
        print(f"📊 生成过去{hours}小时的Hacker News报告...")

        try:
            report_file = await self.update_service.generate_hourly_report(hours)

            if report_file:
                print(f"✅ 报告生成成功: {report_file}")

                # 显示报告内容预览
                try:
                    with open(report_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        preview = content[:500] + "..." if len(content) > 500 else content
                        print(f"\n📄 报告预览:\n{preview}")
                except Exception:
                    pass
            else:
                print("❌ 报告生成失败")

        except Exception as e:
            print(f"❌ 生成报告失败: {str(e)}")

    async def generate_daily_summary(self):
        """生成日度总结"""
        print("📋 生成今日Hacker News总结...")

        try:
            summary_file = await self.update_service.generate_daily_summary()

            if summary_file:
                print(f"✅ 日度总结生成成功: {summary_file}")

                # 显示总结内容预览
                try:
                    with open(summary_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        preview = content[:500] + "..." if len(content) > 500 else content
                        print(f"\n📄 总结预览:\n{preview}")
                except Exception:
                    pass
            else:
                print("❌ 日度总结生成失败")

        except Exception as e:
            print(f"❌ 生成日度总结失败: {str(e)}")

    async def show_status(self):
        """显示服务状态"""
        print("📊 Hacker News监控服务状态:")

        try:
            status = self.update_service.get_status()

            print(f"  服务名称: {status['service_name']}")
            print(f"  状态: {status['status']}")
            print(f"  总报告数: {status.get('total_reports', 0)}")
            print(f"  总结数: {status.get('total_summaries', 0)}")
            print(f"  报告目录: {status.get('reports_directory', 'N/A')}")

            if 'error' in status:
                print(f"  错误: {status['error']}")

        except Exception as e:
            print(f"❌ 获取状态失败: {str(e)}")

    async def show_history(self, limit: int = 5):
        """显示报告历史"""
        print(f"📚 最近{limit}个Hacker News报告:")

        try:
            history = self.update_service.get_report_history(limit)

            if history:
                for i, report_path in enumerate(history, 1):
                    filename = Path(report_path).name
                    print(f"  {i}. {filename}")
            else:
                print("  暂无报告历史")

        except Exception as e:
            print(f"❌ 获取历史失败: {str(e)}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Hacker News CLI 工具")

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 获取最新话题
    latest_parser = subparsers.add_parser('latest', help='获取最新热门话题')
    latest_parser.add_argument('--limit', type=int, default=10, help='显示数量 (默认: 10)')

    # 生成报告
    report_parser = subparsers.add_parser('report', help='生成时间范围报告')
    report_parser.add_argument('--hours', type=int, default=24, help='时间范围(小时) (默认: 24)')

    # 生成日度总结
    subparsers.add_parser('summary', help='生成日度总结')

    # 显示状态
    subparsers.add_parser('status', help='显示服务状态')

    # 显示历史
    history_parser = subparsers.add_parser('history', help='显示报告历史')
    history_parser.add_argument('--limit', type=int, default=5, help='显示数量 (默认: 5)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    cli = HackerNewsCLI()

    try:
        if args.command == 'latest':
            asyncio.run(cli.get_latest_stories(args.limit))
        elif args.command == 'report':
            asyncio.run(cli.generate_report(args.hours))
        elif args.command == 'summary':
            asyncio.run(cli.generate_daily_summary())
        elif args.command == 'status':
            asyncio.run(cli.show_status())
        elif args.command == 'history':
            asyncio.run(cli.show_history(args.limit))
        else:
            print(f"❌ 未知命令: {args.command}")
            parser.print_help()

    except KeyboardInterrupt:
        print("\n❌ 操作被用户中断")
    except Exception as e:
        print(f"❌ 执行失败: {str(e)}")


if __name__ == "__main__":
    main()
