"""
报告生成服务
"""
from datetime import datetime
from typing import List
from pathlib import Path
import json
import logging

from ..models.repository import RepositoryUpdate
from ..models.report import Report
from ..config.settings import Settings


class ReportService:
    """报告生成服务"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.reports_dir = Path(settings.reports_dir)
        self.logger = logging.getLogger(__name__)
        self._ensure_reports_dir()

    def _ensure_reports_dir(self):
        """确保报告目录存在"""
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    async def generate_daily_report(self, updates: List[RepositoryUpdate]) -> Report:
        """生成每日报告"""
        report = Report(
            report_type="daily",
            updates=updates
        )

        # 生成摘要
        report.generate_summary()

        # 保存报告
        await self._save_report(report)

        self.logger.info(f"生成每日报告，包含 {len(updates)} 个更新")
        return report

    async def generate_weekly_report(self, updates: List[RepositoryUpdate]) -> Report:
        """生成每周报告"""
        report = Report(
            report_type="weekly",
            updates=updates
        )

        # 生成摘要
        report.generate_summary()

        # 保存报告
        await self._save_report(report)

        self.logger.info(f"生成每周报告，包含 {len(updates)} 个更新")
        return report

    async def _save_report(self, report: Report):
        """保存报告到文件"""
        try:
            timestamp = report.generated_at.strftime("%Y%m%d_%H%M%S")
            filename = f"{report.report_type}_report_{timestamp}.json"
            file_path = self.reports_dir / filename

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)

            self.logger.debug(f"报告已保存: {file_path}")

        except Exception as e:
            self.logger.error(f"保存报告失败: {e}")

    async def get_recent_reports(self, days: int = 7) -> List[dict]:
        """获取最近的报告"""
        try:
            reports = []
            cutoff_time = datetime.now().timestamp() - (days * 24 * 3600)

            for file_path in self.reports_dir.glob("*_report_*.json"):
                if file_path.stat().st_mtime > cutoff_time:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            report_data = json.load(f)
                            reports.append(report_data)
                    except Exception as e:
                        self.logger.error(f"读取报告文件失败 {file_path}: {e}")

            # 按生成时间排序
            reports.sort(key=lambda x: x.get('generated_at', ''), reverse=True)
            return reports

        except Exception as e:
            self.logger.error(f"获取最近报告失败: {e}")
            return []
