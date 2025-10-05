"""
GitHub Sentinel 主入口文件
"""
import asyncio
import logging
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
from src.services.report_service import ReportService
from src.utils.scheduler import TaskScheduler
from src.utils.logger import setup_logger


class GitHubSentinel:
    def __init__(self, config_path: str = None):
        """初始化GitHub Sentinel"""
        self.settings = Settings.load_from_file(config_path)
        self.logger = setup_logger(self.settings.log_level)

        # 初始化服务
        self.subscription_service = SubscriptionService(self.settings)
        self.update_service = UpdateService(self.settings)
        self.notification_service = NotificationService(self.settings)
        self.report_service = ReportService(self.settings)
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
                report = await self.report_service.generate_daily_report(updates)
                await self.notification_service.send_notifications(report, daily_subs)

                # 更新最后检查时间
                sub_ids = [s.id for s in daily_subs]
                await self.subscription_service.update_last_checked(sub_ids)

                self.logger.info(f"每日扫描完成，处理了 {len(updates)} 个更新")
            else:
                self.logger.info("没有新的更新")

        except Exception as e:
            self.logger.error(f"每日扫描任务失败: {e}", exc_info=True)

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
                report = await self.report_service.generate_weekly_report(updates)
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
            # 调度任务
            self.scheduler.schedule_daily_task(
                self.run_daily_scan,
                time=self.settings.daily_scan_time
            )
            self.scheduler.schedule_weekly_task(
                self.run_weekly_scan,
                day=self.settings.weekly_scan_day,
                time=self.settings.weekly_scan_time
            )

            # 启动调度器
            self.scheduler.start()
            self.logger.info("GitHub Sentinel 已启动，按 Ctrl+C 停止")

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


def main():
    """主函数"""
    app = GitHubSentinel()
    app.start()


if __name__ == "__main__":
    main()
