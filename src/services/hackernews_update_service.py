"""
Hacker News 更新服务 - 简化版（无订阅功能）
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

from ..services.hackernews_service import HackerNewsService
from ..services.hackernews_report_service import HackerNewsReportService
from ..services.notification_service import NotificationService
from ..models.notification import NotificationPayload, NotificationChannel


class HackerNewsUpdateService:
    """Hacker News 更新服务 - 简化版"""

    def __init__(self,
                 notification_service: NotificationService,
                 report_service: HackerNewsReportService):
        self.notification_service = notification_service
        self.report_service = report_service
        self.logger = logging.getLogger(__name__)

        # 报告存储路径
        self.reports_dir = Path("daily_progress")
        self.reports_dir.mkdir(exist_ok=True)

    async def generate_hourly_report(self, hours: int = 24) -> Optional[str]:
        """生成指定时间范围的报告"""
        try:
            self.logger.info(f"开始生成过去{hours}小时的Hacker News报告")

            async with HackerNewsService() as hn_service:
                # 获取指定时间范围内的热门话题
                stories = await hn_service.get_current_hot_topics(hours=hours)

                if not stories:
                    self.logger.info(f"过去{hours}小时内没有找到新的热门话题")
                    return None

                self.logger.info(f"获取到{len(stories)}个热门话题")

                # 生成报告
                timestamp = datetime.now(timezone.utc)
                report = await self.report_service.generate_hourly_report(
                    stories, timestamp, hours
                )

                if report:
                    # 保存报告
                    report_file = await self._save_report(report, timestamp, hours)

                    # 发送通知（可选）
                    await self._send_notification(report, len(stories), hours)

                    self.logger.info(f"Hacker News报告生成完成: {report_file}")
                    return report_file
                else:
                    self.logger.error("报告生成失败")
                    return None

        except Exception as e:
            self.logger.error(f"生成Hacker News报告失败: {str(e)}")
            return None

    async def generate_daily_summary(self, date: Optional[datetime] = None) -> Optional[str]:
        """生成日度总结报告"""
        try:
            if date is None:
                date = datetime.now(timezone.utc).date()
            else:
                date = date.date() if hasattr(date, 'date') else date

            self.logger.info(f"开始生成{date}的Hacker News日度总结")

            # 收集全天的数据（24小时）
            start_time = datetime.combine(date, datetime.min.time()).replace(tzinfo=timezone.utc)
            end_time = start_time + timedelta(days=1)

            async with HackerNewsService() as hn_service:
                # 获取全天的热门话题
                all_stories = await hn_service.get_current_hot_topics(hours=24)

                if not all_stories:
                    self.logger.info(f"{date}没有找到热门话题数据")
                    return None

                # 生成日度总结
                summary = await self.report_service.generate_daily_summary(
                    all_stories, datetime.combine(date, datetime.min.time())
                )

                if summary:
                    # 保存总结
                    summary_file = await self._save_daily_summary(summary, date)
                    self.logger.info(f"Hacker News日度总结生成完成: {summary_file}")
                    return summary_file
                else:
                    self.logger.error("日度总结生成失败")
                    return None

        except Exception as e:
            self.logger.error(f"生成Hacker News日度总结失败: {str(e)}")
            return None

    async def _save_report(self, report: str, timestamp: datetime, hours: int) -> str:
        """保存小时报告到文件"""
        try:
            date_str = timestamp.strftime('%Y%m%d')
            time_str = timestamp.strftime('%H%M%S')
            filename = f"hackernews_{hours}h_{date_str}_{time_str}.md"

            report_path = self.reports_dir / filename
            report_path.write_text(report, encoding='utf-8')

            self.logger.info(f"Hacker News报告已保存: {report_path}")
            return str(report_path)

        except Exception as e:
            self.logger.error(f"保存Hacker News报告失败: {str(e)}")
            return ""

    async def _save_daily_summary(self, summary: str, date) -> str:
        """保存日度总结到文件"""
        try:
            date_str = date.strftime('%Y%m%d')
            filename = f"hackernews_summary_{date_str}.md"

            summary_path = self.reports_dir / filename
            summary_path.write_text(summary, encoding='utf-8')

            self.logger.info(f"Hacker News日度总结已保存: {summary_path}")
            return str(summary_path)

        except Exception as e:
            self.logger.error(f"保存Hacker News日度总结失败: {str(e)}")
            return ""

    async def _send_notification(self, report: str, story_count: int, hours: int):
        """发送通知（可选功能）"""
        try:
            notification_payload = NotificationPayload(
                channel=NotificationChannel.EMAIL,
                subject=f"Hacker News 热门话题更新 - 过去{hours}小时",
                body=report[:500] + "..." if len(report) > 500 else report,  # 限制通知内容长度
                metadata={
                    'story_count': story_count,
                    'time_range_hours': hours,
                    'report_type': 'hourly',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            )

            # 发送通知
            await self.notification_service.send_notification(notification_payload)

        except Exception as e:
            self.logger.error(f"发送Hacker News通知失败: {str(e)}")

    async def get_latest_stories(self, limit: int = 30) -> List[Dict[str, Any]]:
        """获取最新的热门话题（用于Web界面等）"""
        try:
            async with HackerNewsService() as hn_service:
                stories = await hn_service.get_top_stories_details(limit)

                # 转换为字典格式便于JSON序列化
                return [story.to_dict() for story in stories]

        except Exception as e:
            self.logger.error(f"获取最新Hacker News话题失败: {str(e)}")
            return []

    async def get_stories_in_range(self, hours: int = 24) -> List[Dict[str, Any]]:
        """获取指定时间范围内的话题"""
        try:
            async with HackerNewsService() as hn_service:
                stories = await hn_service.get_current_hot_topics(hours=hours)

                return [story.to_dict() for story in stories]

        except Exception as e:
            self.logger.error(f"获取时间范围内的Hacker News话题失败: {str(e)}")
            return []

    def get_report_history(self, limit: int = 10) -> List[str]:
        """获取报告历史"""
        try:
            report_files = list(self.reports_dir.glob("hackernews_*.md"))
            report_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            return [str(f) for f in report_files[:limit]]

        except Exception as e:
            self.logger.error(f"获取Hacker News报告历史失败: {str(e)}")
            return []

    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        try:
            status = {
                "service_name": "Hacker News Update Service",
                "status": "active",
                "reports_directory": str(self.reports_dir),
                "total_reports": 0,
                "total_summaries": 0,
                "latest_report": None,
                "latest_summary": None
            }

            # 统计报告文件
            if self.reports_dir.exists():
                report_files = list(self.reports_dir.glob("hackernews_*h_*.md"))
                summary_files = list(self.reports_dir.glob("hackernews_summary_*.md"))

                status["total_reports"] = len(report_files)
                status["total_summaries"] = len(summary_files)

                # 获取最新的报告和总结
                if report_files:
                    latest_report = max(report_files, key=lambda x: x.stat().st_mtime)
                    status["latest_report"] = latest_report.name

                if summary_files:
                    latest_summary = max(summary_files, key=lambda x: x.stat().st_mtime)
                    status["latest_summary"] = latest_summary.name

            return status

        except Exception as e:
            self.logger.error(f"获取Hacker News服务状态失败: {str(e)}")
            return {
                "service_name": "Hacker News Update Service",
                "status": "error",
                "error": str(e)
            }

    def cleanup_old_reports(self, days_to_keep: int = 30):
        """清理旧报告文件"""
        try:
            cutoff_time = datetime.now() - timedelta(days=days_to_keep)

            if not self.reports_dir.exists():
                return

            removed_count = 0
            for report_file in self.reports_dir.glob("hackernews_*.md"):
                if datetime.fromtimestamp(report_file.stat().st_mtime) < cutoff_time:
                    report_file.unlink()
                    removed_count += 1

            if removed_count > 0:
                self.logger.info(f"已清理{removed_count}个旧的Hacker News报告文件")

        except Exception as e:
            self.logger.error(f"清理旧报告文件失败: {str(e)}")

    async def test_connection(self) -> bool:
        """测试Hacker News API连接"""
        try:
            async with HackerNewsService() as hn_service:
                # 尝试获取一个话题来测试连接
                test_stories = await hn_service.get_top_stories_details(1)
                return len(test_stories) > 0
        except Exception as e:
            self.logger.error(f"测试Hacker News连接失败: {str(e)}")
            return False

