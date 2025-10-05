"""
报告数据模型
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from .repository import RepositoryUpdate


@dataclass
class Report:
    """报告模型"""
    report_type: str  # daily, weekly, custom
    generated_at: datetime = field(default_factory=datetime.now)
    updates: List[RepositoryUpdate] = field(default_factory=list)
    summary: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'report_type': self.report_type,
            'generated_at': self.generated_at.isoformat(),
            'updates': [update.to_dict() for update in self.updates],
            'summary': self.summary
        }

    def generate_summary(self) -> Dict[str, Any]:
        """生成报告摘要"""
        if not self.updates:
            return {
                'total_updates': 0,
                'repositories_count': 0,
                'update_types': {},
                'top_contributors': []
            }

        # 统计更新类型
        update_types = {}
        repositories = set()
        contributors = {}

        for update in self.updates:
            # 统计更新类型
            update_type = update.update_type
            update_types[update_type] = update_types.get(update_type, 0) + 1

            # 统计仓库
            repositories.add(f"{update.owner}/{update.repo_name}")

            # 统计贡献者
            contributors[update.author] = contributors.get(update.author, 0) + 1

        # 排序贡献者
        top_contributors = sorted(contributors.items(), key=lambda x: x[1], reverse=True)[:5]

        summary = {
            'total_updates': len(self.updates),
            'repositories_count': len(repositories),
            'update_types': update_types,
            'top_contributors': [{'author': author, 'count': count} for author, count in top_contributors],
            'repositories': list(repositories)
        }

        self.summary = summary
        return summary

    def to_text(self) -> str:
        """转换为文本格式"""
        if not self.updates:
            return f"📊 {self.report_type.upper()} 报告 - {self.generated_at.strftime('%Y-%m-%d %H:%M')}\n\n暂无更新"

        summary = self.summary or self.generate_summary()

        lines = [
            f"📊 {self.report_type.upper()} 报告 - {self.generated_at.strftime('%Y-%m-%d %H:%M')}",
            "",
            "📈 摘要:",
            f"  • 总更新数: {summary['total_updates']}",
            f"  • 涉及仓库: {summary['repositories_count']}",
            ""
        ]

        # 更新类型统计
        if summary['update_types']:
            lines.append("📋 更新类型分布:")
            for update_type, count in summary['update_types'].items():
                icon = self._get_update_type_icon(update_type)
                lines.append(f"  {icon} {update_type}: {count}")
            lines.append("")

        # 活跃贡献者
        if summary['top_contributors']:
            lines.append("👥 活跃贡献者:")
            for contributor in summary['top_contributors']:
                lines.append(f"  • {contributor['author']}: {contributor['count']} 次贡献")
            lines.append("")

        # 详细更新列表
        lines.append("📝 详细更新:")
        grouped_updates = self._group_updates_by_repo()

        for repo, updates in grouped_updates.items():
            lines.append(f"\n🔗 {repo}")
            for update in updates:
                icon = self._get_update_type_icon(update.update_type)
                lines.append(f"  {icon} {update.title[:80]}{'...' if len(update.title) > 80 else ''}")
                lines.append(f"     👤 {update.author} • 🕒 {update.created_at.strftime('%m-%d %H:%M')}")

        return "\n".join(lines)

    def to_html(self) -> str:
        """转换为HTML格式"""
        if not self.updates:
            return f"""
            <h2>📊 {self.report_type.upper()} 报告</h2>
            <p><em>生成时间: {self.generated_at.strftime('%Y-%m-%d %H:%M')}</em></p>
            <p>暂无更新</p>
            """

        summary = self.summary or self.generate_summary()

        html_parts = [
            f"<h2>📊 {self.report_type.upper()} 报告</h2>",
            f"<p><em>生成时间: {self.generated_at.strftime('%Y-%m-%d %H:%M')}</em></p>",

            "<h3>📈 摘要</h3>",
            "<ul>",
            f"<li>总更新数: <strong>{summary['total_updates']}</strong></li>",
            f"<li>涉及仓库: <strong>{summary['repositories_count']}</strong></li>",
            "</ul>"
        ]

        # 更新类型统计
        if summary['update_types']:
            html_parts.extend([
                "<h3>📋 更新类型分布</h3>",
                "<ul>"
            ])
            for update_type, count in summary['update_types'].items():
                icon = self._get_update_type_icon(update_type)
                html_parts.append(f"<li>{icon} {update_type}: <strong>{count}</strong></li>")
            html_parts.append("</ul>")

        # 活跃贡献者
        if summary['top_contributors']:
            html_parts.extend([
                "<h3>👥 活跃贡献者</h3>",
                "<ul>"
            ])
            for contributor in summary['top_contributors']:
                html_parts.append(f"<li>{contributor['author']}: <strong>{contributor['count']}</strong> 次贡献</li>")
            html_parts.append("</ul>")

        # 详细更新列表
        html_parts.append("<h3>📝 详细更新</h3>")
        grouped_updates = self._group_updates_by_repo()

        for repo, updates in grouped_updates.items():
            html_parts.extend([
                f"<h4>🔗 {repo}</h4>",
                "<ul>"
            ])
            for update in updates:
                icon = self._get_update_type_icon(update.update_type)
                html_parts.append(
                    f"<li>{icon} <a href='{update.url}' target='_blank'>{update.title}</a><br>"
                    f"<small>👤 {update.author} • 🕒 {update.created_at.strftime('%m-%d %H:%M')}</small></li>"
                )
            html_parts.append("</ul>")

        return "\n".join(html_parts)

    def _group_updates_by_repo(self) -> Dict[str, List[RepositoryUpdate]]:
        """按仓库分组更新"""
        grouped = {}
        for update in self.updates:
            repo_key = f"{update.owner}/{update.repo_name}"
            if repo_key not in grouped:
                grouped[repo_key] = []
            grouped[repo_key].append(update)

        # 按时间排序每个仓库的更新
        for repo_updates in grouped.values():
            repo_updates.sort(key=lambda x: x.created_at, reverse=True)

        return grouped

    def _get_update_type_icon(self, update_type: str) -> str:
        """获取更新类型图标"""
        icons = {
            'commits': '💾',
            'issues': '🐛',
            'pull_requests': '🔄',
            'releases': '🚀'
        }
        return icons.get(update_type, '📌')
