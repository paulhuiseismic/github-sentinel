"""
报告生成服务
"""
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import json
import logging

from ..models.repository import RepositoryUpdate
from ..models.report import Report
from ..services.llm_service import LLMService
from ..services.github_service import GitHubService


class ReportService:
    """报告生成服务"""

    def __init__(self, llm_service: LLMService, github_service: GitHubService):
        self.llm_service = llm_service
        self.github_service = github_service
        self.reports_dir = Path("data/reports")
        self.daily_progress_dir = Path("daily_progress")
        self.logger = logging.getLogger(__name__)
        self._ensure_dirs()

    def _ensure_dirs(self):
        """确保必要目录存在"""
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.daily_progress_dir.mkdir(parents=True, exist_ok=True)

    async def generate_daily_progress_report(self, owner: str, repo: str,
                                           since: Optional[datetime] = None,
                                           until: Optional[datetime] = None,
                                           compact_mode: bool = True) -> str:
        """生成每日进展报告（原始数据）"""
        try:
            # 使用GitHub服务导出每日进展，默认使用紧凑模式
            progress_file = await self.github_service.export_daily_progress(
                owner, repo, str(self.daily_progress_dir),
                since=since, until=until, compact_mode=compact_mode
            )

            self.logger.info(f"每日进展报告已生成: {progress_file}")
            return progress_file

        except Exception as e:
            self.logger.error(f"生成每日进展报告失败: {str(e)}")
            raise

    async def generate_llm_summary_report(self,
                                         repo: str,
                                         progress_file: str,
                                         template_name: str = "github_azure_prompt.txt",
                                         provider_name: Optional[str] = None,
                                         max_tokens: int = 1500,  # 降低默认token数量
                                         **llm_kwargs) -> str:
        """使用LLM生成摘要报告"""
        try:
            # 读取进展文件内容
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress_content = f.read()

            # 检查内容长度，如果太长则截断
            if len(progress_content) > 4000:  # 约1000个token
                self.logger.warning(f"进展内容过长({len(progress_content)}字符)，将截断以节省token")
                progress_content = progress_content[:4000] + "\n\n[内容已截断以节省token]"

            # 使用LLM生成摘要报告，设置较小的max_tokens
            summary_file = await self.llm_service.generate_summary_report(
                repo_name=repo,
                markdown_content=progress_content,
                template_name=template_name,
                provider_name=provider_name,
                output_dir=str(self.daily_progress_dir),
                max_tokens=max_tokens,
                **llm_kwargs
            )

            self.logger.info(f"LLM摘要报告已生成: {summary_file}")
            return summary_file

        except Exception as e:
            self.logger.error(f"生成LLM摘要报告失败: {str(e)}")
            raise

    async def generate_complete_daily_report(self,
                                           owner: str,
                                           repo: str,
                                           template_name: str = "github_azure_prompt.txt",
                                           provider_name: Optional[str] = None,
                                           since: Optional[datetime] = None,
                                           until: Optional[datetime] = None,
                                           compact_mode: bool = True,
                                           max_tokens: int = 1500,
                                           **llm_kwargs) -> Dict[str, str]:
        """生成完整的每日报告（包括原始数据和LLM摘要）"""
        try:
            # 1. 生成原始进展报告（使用紧凑模式）
            progress_file = await self.generate_daily_progress_report(
                owner, repo, since=since, until=until, compact_mode=compact_mode
            )

            # 2. 生成LLM摘要报告（使用较小的token数量）
            summary_file = await self.generate_llm_summary_report(
                repo, progress_file, template_name, provider_name,
                max_tokens=max_tokens, **llm_kwargs
            )

            return {
                "progress_report": progress_file,
                "summary_report": summary_file,
                "repository": f"{owner}/{repo}",
                "generated_at": datetime.now().isoformat(),
                "mode": "compact" if compact_mode else "full",
                "time_range": f"{since or 'auto'} to {until or 'now'}"
            }

        except Exception as e:
            self.logger.error(f"生成完整每日报告失败: {str(e)}")
            raise

    async def batch_generate_reports(self,
                                   repositories: List[Dict[str, str]],
                                   template_name: str = "github_azure_prompt.txt",
                                   provider_name: Optional[str] = None,
                                   **llm_kwargs) -> List[Dict[str, str]]:
        """批量生成多个仓库的报告"""
        results = []

        for repo_info in repositories:
            owner = repo_info.get('owner')
            repo = repo_info.get('repo')

            if not owner or not repo:
                self.logger.warning(f"跳过无效的仓库信息: {repo_info}")
                continue

            try:
                result = await self.generate_complete_daily_report(
                    owner, repo, template_name, provider_name, **llm_kwargs
                )
                results.append(result)
                self.logger.info(f"已完成 {owner}/{repo} 的报告生成")

            except Exception as e:
                self.logger.error(f"生成 {owner}/{repo} 报告失败: {str(e)}")
                results.append({
                    "repository": f"{owner}/{repo}",
                    "error": str(e),
                    "generated_at": datetime.now().isoformat()
                })

        return results

    async def generate_report_with_multiple_templates(self,
                                                    owner: str,
                                                    repo: str,
                                                    templates: List[str],
                                                    provider_name: Optional[str] = None) -> Dict[str, str]:
        """使用多个模板生成对比报告"""
        try:
            # 先生成原始进展报告（使用紧凑模式节省token）
            progress_file = await self.generate_daily_progress_report(
                owner, repo, compact_mode=True
            )

            summaries = {}
            for template in templates:
                try:
                    summary_file = await self.generate_llm_summary_report(
                        repo, progress_file, template, provider_name, max_tokens=1200
                    )
                    summaries[template] = summary_file
                except Exception as e:
                    summaries[template] = f"ERROR: {str(e)}"

            return {
                "progress_report": progress_file,
                "summaries": summaries,
                "repository": f"{owner}/{repo}",
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"生成多模板对比报告失败: {str(e)}")
            raise

    def get_report_history(self, repo: str, limit: int = 10) -> List[str]:
        """获取指定仓库的报告历史"""
        try:
            pattern = f"{repo}_*.md"
            files = list(self.daily_progress_dir.glob(pattern))
            # 按文件名排序（包含日期）
            files.sort(key=lambda x: x.name, reverse=True)
            return [str(f) for f in files[:limit]]
        except Exception as e:
            self.logger.error(f"获取报告历史失败: {str(e)}")
            return []

    def export_report_summary(self, reports: List[Dict], output_file: Optional[str] = None) -> str:
        """导出报告摘要到JSON文件"""
        try:
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = str(self.reports_dir / f"report_summary_{timestamp}.json")

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(reports, f, indent=2, ensure_ascii=False, default=str)

            self.logger.info(f"报告摘要已导出: {output_file}")
            return output_file

        except Exception as e:
            self.logger.error(f"导出报告摘要失败: {str(e)}")
            raise

    async def generate_legacy_report(self, updates: List[RepositoryUpdate]) -> Report:
        """生成传统格式报告（保持向后兼容）"""
        report = Report(
            report_type="daily",
            updates=updates
        )

        # 生成摘要
        report.generate_summary()

        # 保存报告
        await self._save_legacy_report(report)

        self.logger.info(f"生成传统格式报告，包含 {len(updates)} 个更新")
        return report

    async def _save_legacy_report(self, report: Report):
        """保存传统格式报告"""
        filename = f"daily_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.reports_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2, default=str)

        self.logger.info(f"报告已保存到: {filepath}")
