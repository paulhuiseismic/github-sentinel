"""
GitHub Sentinel 主入口文件
"""
import asyncio
import signal
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import Settings
from src.services.subscription_service import SubscriptionService
from src.services.update_service import UpdateService
from src.services.notification_service import NotificationService
from src.services.llm_service import LLMService
from src.services.report_service import ReportService
from src.services.github_service import GitHubService
from src.services.web_service import WebService
from src.services.hackernews_service import HackerNewsService
from src.services.hackernews_report_service import HackerNewsReportService
from src.services.hackernews_update_service import HackerNewsUpdateService
from src.utils.scheduler import TaskScheduler
from src.utils.logger import get_main_logger


class GitHubSentinel:
    def __init__(self, config_path: str = None):
        """初始化GitHub Sentinel"""
        self.settings = Settings.from_config_file(config_path)
        # 使用专用的主程序logger
        self.logger = get_main_logger(self.settings.log_level)

        # 记录启动信息
        self.logger.info("=" * 50)
        self.logger.info("GitHub Sentinel 初始化中...")
        self.logger.info(f"配置文件: {config_path or '默认配置'}")
        self.logger.info(f"日志级别: {self.settings.log_level}")

        # 初始化服务
        self.subscription_service = SubscriptionService(self.settings)

        # 修复GitHubService初始化 - 更好的token获取和验证
        github_token = ""
        if hasattr(self.settings, 'github') and hasattr(self.settings.github, 'token'):
            github_token = self.settings.github.token or ""

        # 验证token是否有效
        if not github_token or github_token == "null" or github_token.strip() == "":
            self.logger.warning("⚠️  GitHub Token未设置或无效！")
            self.logger.warning("请设置环境变量 GITHUB_TOKEN 或在配置文件中提供有效的token")
            self.logger.warning("获取GitHub Token: https://github.com/settings/tokens")
            # 使用空token创建服务，但会在使用时提供友好的错误信息
            github_token = ""
        else:
            self.logger.info("✅ GitHub Token已配置")

        self.github_service = GitHubService(github_token)
        self.update_service = UpdateService(self.settings)
        self.notification_service = NotificationService(self.settings)
        # 修复ReportService初始化
        self.llm_service = LLMService()
        self.report_service = ReportService(self.llm_service, self.github_service)

        # 初始化Hacker News相关服务
        self.hn_report_service = HackerNewsReportService(self.llm_service)
        self.hn_update_service = HackerNewsUpdateService(
            self.notification_service,
            self.hn_report_service
        )

        self.web_service = WebService(self.settings)
        self.scheduler = TaskScheduler()

        # 设置信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """处理系统信号"""
        self.logger.info(f"收到信号 {signum}，正在关闭...")
        self.stop()
        sys.exit(0)

    async def run_daily_scan(self):
        """执行每日扫描任务"""
        try:
            self.logger.info("开始执行每日扫描任务")
            subscriptions = await self.subscription_service.get_active_subscriptions()

            if not subscriptions:
                self.logger.info("没有活跃的订阅，跳过扫描")
                return

            # 获取每日更新的订阅
            daily_subs = [s for s in subscriptions if s.frequency.value in ['daily', 'both']]
            if not daily_subs:
                self.logger.info("没有每日扫描的订阅")
                return

            updates = await self.update_service.fetch_updates(daily_subs, days=1)
            if updates:
                report = await self.report_service.generate_report(updates, "daily")
                await self.notification_service.send_notifications(report, daily_subs)

                # 更新最后检查时间
                sub_ids = [s.id for s in daily_subs]
                await self.subscription_service.update_last_checked(sub_ids)

                self.logger.info(f"每日扫描完成，处理了 {len(updates)} 个更新")
            else:
                self.logger.info("没有新的更新")

        except Exception as e:
            self.logger.error(f"每日扫描任务失败: {e}", exc_info=True)

    async def run_hackernews_scan(self, hours: int = 24):
        """执行Hacker News扫描任务"""
        try:
            self.logger.info(f"开始执行Hacker News扫描任务 - 过去{hours}小时")

            # 生成报告
            report_file = await self.hn_update_service.generate_hourly_report(hours=hours)

            if report_file:
                self.logger.info(f"Hacker News扫描完成，报告已保存: {report_file}")
            else:
                self.logger.info("Hacker News扫描完成，但没有生成新报告")

        except Exception as e:
            self.logger.error(f"Hacker News扫描任务失败: {e}", exc_info=True)

    async def run_hackernews_daily_summary(self):
        """生成Hacker News日度总结"""
        try:
            self.logger.info("开始生成Hacker News日度总结")
            from datetime import datetime, timezone

            # 生成当天的总结
            today = datetime.now(timezone.utc)
            summary_file = await self.hn_update_service.generate_daily_summary(today)

            if summary_file:
                self.logger.info(f"Hacker News日度总结生成完成: {summary_file}")
            else:
                self.logger.info("没有生成Hacker News日度总结")

        except Exception as e:
            self.logger.error(f"生成Hacker News日度总结失败: {e}", exc_info=True)

    async def run_weekly_scan(self):
        """执行每周扫描任务"""
        try:
            self.logger.info("开始执行每周扫描任务")
            subscriptions = await self.subscription_service.get_active_subscriptions()

            # 获取每周更新的订阅
            weekly_subs = [s for s in subscriptions if s.frequency.value in ['weekly', 'both']]
            if not weekly_subs:
                self.logger.info("没有每周扫描的订阅")
                return

            updates = await self.update_service.fetch_updates(weekly_subs, days=7)

            if updates:
                report = await self.report_service.generate_report(updates, "weekly")
                await self.notification_service.send_notifications(report, weekly_subs)

                # 更新最后检查时间
                sub_ids = [s.id for s in weekly_subs]
                await self.subscription_service.update_last_checked(sub_ids)

                self.logger.info(f"每周扫描完成，处理了 {len(updates)} 个更新")
            else:
                self.logger.info("没有新的更新")

        except Exception as e:
            self.logger.error(f"每周扫描任务失败: {e}", exc_info=True)

    def start(self):
        """启动应用"""
        self.logger.info("GitHub Sentinel 启动中...")

        try:
            # 调度任务 - 使用默认时间配置
            daily_time = getattr(self.settings, 'daily_scan_time', "09:00")
            weekly_day = getattr(self.settings, 'weekly_scan_day', "monday")
            weekly_time = getattr(self.settings, 'weekly_scan_time', "10:00")

            # GitHub监控任务
            self.scheduler.schedule_daily_task(
                self.run_daily_scan,
                time=daily_time
            )
            self.scheduler.schedule_weekly_task(
                self.run_weekly_scan,
                day=weekly_day,
                time=weekly_time
            )

            # Hacker News监控任务 - 每小时执行一次
            self.scheduler.schedule_hourly_task(
                self.run_hackernews_scan,
                minute=0  # 每小时的0分执行
            )

            # Hacker News日度总结 - 每天23:30生成
            self.scheduler.schedule_daily_task(
                self.run_hackernews_daily_summary,
                time="23:30"
            )

            # 启动调度器
            self.scheduler.start()
            self.logger.info("GitHub Sentinel 已启动，按 Ctrl+C 停止")
            self.logger.info("✅ GitHub监控: 每日/每周扫描已启用")
            self.logger.info("✅ Hacker News监控: 每小时扫描已启用")

            # 保持主线程运行
            try:
                while self.scheduler.is_running:
                    asyncio.get_event_loop().run_until_complete(asyncio.sleep(60))
            except KeyboardInterrupt:
                self.stop()

        except Exception as e:
            self.logger.error(f"启动失败: {e}", exc_info=True)
            self.stop()

    def stop(self):
        """停止应用"""
        self.logger.info("正在停止 GitHub Sentinel...")
        if hasattr(self, 'scheduler'):
            self.scheduler.stop()
        self.logger.info("GitHub Sentinel 已停止")

    def start_web(self, server_name: str = "0.0.0.0", server_port: int = 7860, share: bool = False):
        """启动Web界面"""
        self.logger.info("启动GitHub Sentinel Web界面...")
        try:
            self.web_service.launch(server_name=server_name, server_port=server_port, share=share)
        except ImportError as e:
            self.logger.error("缺少Web界面依赖，请安装: pip install gradio>=4.0.0 pandas")
            raise e
        except Exception as e:
            self.logger.error(f"启动Web界面失败: {e}")
            raise e


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="GitHub Sentinel - 智能GitHub仓库监控系统")
    parser.add_argument("--config", "-c", help="配置文件路径")
    parser.add_argument("--web", action="store_true", help="启动Web界面")
    parser.add_argument("--port", type=int, default=7860, help="Web界面端口 (默认: 7860)")
    parser.add_argument("--host", default="0.0.0.0", help="Web界面主机 (默认: 0.0.0.0)")
    parser.add_argument("--share", action="store_true", help="创建公共分享链接")

    args = parser.parse_args()

    sentinel = GitHubSentinel(args.config)

    if args.web:
        # 启动Web界面
        sentinel.start_web(server_name=args.host, server_port=args.port, share=args.share)
    else:
        # 启动后台服务
        sentinel.start()


if __name__ == "__main__":
    main()
