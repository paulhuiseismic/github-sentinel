"""
Hacker News 报告服务
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pathlib import Path

from ..models.hackernews import HackerNewsItem
from ..services.llm_service import LLMService


class HackerNewsReportService:
    """Hacker News 报告生成服务"""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.logger = logging.getLogger(__name__)
        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        """加载Hacker News分析prompt模板"""
        try:
            prompt_path = Path(__file__).parent.parent.parent / "prompts" / "hacker_news_hours_topic_azure_prompt.txt"
            if prompt_path.exists():
                return prompt_path.read_text(encoding='utf-8')
            else:
                self.logger.warning(f"未找到prompt文件: {prompt_path}")
                return self._get_default_prompt_template()
        except Exception as e:
            self.logger.error(f"加载prompt模板失败: {str(e)}")
            return self._get_default_prompt_template()

    def _get_default_prompt_template(self) -> str:
        """获取默认的prompt模板"""
        return """你是一个关注 Hacker News 的技术专家，擅于洞察技术热点和发展趋势。

任务：
1.根据你收到的 Hacker News Top List，分析和总结当前技术圈讨论的热点话题。
2.使用中文生成报告，内容仅包含5个热点话题，并保留原始链接。

格式：
# Hacker News 热门话题 {日期} {小时}

请按照以下格式分析热点话题：
1. **话题标题**：话题描述和分析
    - 相关链接

请确保：
- 选择最具代表性和讨论度高的话题
- 提供深入的技术洞察
- 保留原始链接以便读者进一步了解
"""

    def _format_stories_for_llm(self, stories: List[HackerNewsItem]) -> str:
        """将故事列表格式化为LLM输入"""
        if not stories:
            return "暂无Hacker News数据"

        formatted_stories = []
        for i, story in enumerate(stories, 1):
            story_text = f"{i}. **{story.title}**"
            if story.url:
                story_text += f"\n   URL: {story.url}"
            story_text += f"\n   分数: {story.score}, 评论: {story.descendants}, 作者: {story.by}"
            story_text += f"\n   发布时间: {story.time.strftime('%Y-%m-%d %H:%M UTC')}"
            if story.text:
                # 限制文本长度，避免过长
                text_preview = story.text[:200] + "..." if len(story.text) > 200 else story.text
                story_text += f"\n   内容摘要: {text_preview}"
            formatted_stories.append(story_text)

        return "\n\n".join(formatted_stories)

    async def generate_hourly_report(self,
                                   stories: List[HackerNewsItem],
                                   timestamp: datetime,
                                   hours: int = 24) -> str:
        """生成指定时间范围的报告"""
        if not stories:
            return f"# Hacker News 热门话题 {timestamp.strftime('%Y-%m-%d %H:%M')}\n\n过去{hours}小时暂无新的热门话题。"

        try:
            # 格式化输入数据
            stories_text = self._format_stories_for_llm(stories)

            # 构建完整prompt
            date_str = timestamp.strftime('%Y-%m-%d')
            hour_str = timestamp.strftime('%H:%M')

            # 使用加载的prompt模板
            full_prompt = f"""{self.prompt_template}

当前时间: {date_str} {hour_str}
分析范围: 过去{hours}小时

Hacker News Top Stories:
{stories_text}

请根据以上内容生成热门话题分析报告，严格按照模板格式输出。"""

            self.logger.info(f"正在使用LLM生成Hacker News报告，包含{len(stories)}个故事")

            # 调用LLM生成报告
            report = await self.llm_service.generate_text(
                prompt=full_prompt,
                max_tokens=2000,
                temperature=0.7
            )

            if report:
                self.logger.info("LLM报告生成成功")
                return report
            else:
                self.logger.warning("LLM返回空结果，使用备用报告")
                return self._generate_fallback_report(stories, timestamp, hours)

        except Exception as e:
            self.logger.error(f"生成Hacker News报告失败: {str(e)}")
            return self._generate_fallback_report(stories, timestamp, hours)

    def _generate_fallback_report(self,
                                stories: List[HackerNewsItem],
                                timestamp: datetime,
                                hours: int = 24) -> str:
        """生成备用报告（当LLM失败时）"""
        date_str = timestamp.strftime('%Y-%m-%d')
        hour_str = timestamp.strftime('%H:%M')

        report = f"# Hacker News 热门话题 {date_str} {hour_str}\n\n"
        report += f"*以下是过去{hours}小时的热门话题汇总*\n\n"

        # 选择前5个最高分的故事
        top_stories = sorted(stories, key=lambda x: x.score, reverse=True)[:5]

        for i, story in enumerate(top_stories, 1):
            report += f"{i}. **{story.title}**：分数 {story.score}，评论 {story.descendants}\n"
            if story.url:
                report += f"    - {story.url}\n"
            report += "\n"

        report += f"\n---\n*报告生成时间: {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}*\n"
        report += f"*数据来源: Hacker News (https://news.ycombinator.com)*"

        return report

    async def generate_daily_summary(self,
                                   all_stories: List[HackerNewsItem],
                                   date: datetime) -> str:
        """生成日度总结报告"""
        if not all_stories:
            return f"# Hacker News 日度总结 {date.strftime('%Y-%m-%d')}\n\n今日暂无热门话题数据。"

        try:
            # 按分数和评论数筛选出最重要的话题
            important_stories = sorted(all_stories, key=lambda x: (x.score + x.descendants), reverse=True)[:10]

            stories_text = self._format_stories_for_llm(important_stories)

            summary_prompt = f"""你是一个关注 Hacker News 的技术专家，擅于洞察技术热点和发展趋势。

请基于以下Hacker News全天数据，生成一份日度总结报告。

要求：
1. 识别全天最重要的技术趋势和话题
2. 合并重复或相关的话题  
3. 突出最具影响力的讨论
4. 使用中文，保持专业分析风格
5. 保留重要链接
6. 总结不超过5个主要话题

格式：
# Hacker News 日度总结 {date.strftime('%Y-%m-%d')}

日期: {date.strftime('%Y-%m-%d')}

全天重要话题数据:
{stories_text}

请生成日度总结报告："""

            summary = await self.llm_service.generate_text(
                prompt=summary_prompt,
                max_tokens=1500,
                temperature=0.6
            )

            return summary if summary else self._generate_fallback_daily_summary(all_stories, date)

        except Exception as e:
            self.logger.error(f"生成Hacker News日度总结失败: {str(e)}")
            return self._generate_fallback_daily_summary(all_stories, date)

    def _generate_fallback_daily_summary(self, stories: List[HackerNewsItem], date: datetime) -> str:
        """生成备用日度总结"""
        top_stories = sorted(stories, key=lambda x: x.score, reverse=True)[:5]

        report = f"# Hacker News 日度总结 {date.strftime('%Y-%m-%d')}\n\n"
        report += "## 全天热门话题\n\n"

        for i, story in enumerate(top_stories, 1):
            report += f"{i}. **{story.title}**\n"
            report += f"   - 分数: {story.score}, 评论: {story.descendants}\n"
            if story.url:
                report += f"   - 链接: {story.url}\n"
            report += "\n"

        report += f"## 数据统计\n\n"
        report += f"- 总话题数: {len(stories)}\n"
        report += f"- 平均分数: {sum(s.score for s in stories) // len(stories) if stories else 0}\n"
        report += f"- 总评论数: {sum(s.descendants for s in stories)}\n"

        report += f"\n---\n*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        report += f"*数据来源: Hacker News*"

        return report
