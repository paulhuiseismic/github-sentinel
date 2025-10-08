"""
GitHub API 服务
"""
import aiohttp
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta, timezone
import logging
import json
import os
from pathlib import Path

from ..models.repository import Repository, RepositoryUpdate


class GitHubService:
    """GitHub API 服务类"""

    def __init__(self, token: str, rate_limit_per_hour: int = 5000, timeout: int = 30):
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "GitHub-Sentinel/1.0"
        }
        self.rate_limit_per_hour = rate_limit_per_hour
        self.requests_made = 0
        self.last_reset = datetime.now()
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)

    async def _check_rate_limit(self):
        """检查API速率限制"""
        now = datetime.now()
        if (now - self.last_reset).total_seconds() > 3600:
            self.requests_made = 0
            self.last_reset = now

        if self.requests_made >= self.rate_limit_per_hour:
            wait_time = 3600 - (now - self.last_reset).total_seconds()
            if wait_time > 0:
                self.logger.warning(f"达到速率限制，等待 {wait_time:.0f} 秒")
                await asyncio.sleep(wait_time)
                self.requests_made = 0
                self.last_reset = datetime.now()

    async def _make_request(self, url: str, params: Optional[Dict] = None) -> Dict:
        """发起API请求"""
        await self._check_rate_limit()

        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.get(url, headers=self.headers, params=params) as response:
                    self.requests_made += 1

                    if response.status == 200:
                        return await response.json()
                    elif response.status == 403:
                        self.logger.error(f"API访问被拒绝: {response.status}")
                        raise Exception(f"GitHub API访问被拒绝: {response.status}")
                    elif response.status == 404:
                        self.logger.error(f"资源未找到: {url}")
                        raise Exception(f"GitHub资源未找到: {url}")
                    else:
                        self.logger.error(f"API请求失败: {response.status}")
                        raise Exception(f"GitHub API请求失败: {response.status}")

            except asyncio.TimeoutError:
                self.logger.error(f"请求超时: {url}")
                raise Exception(f"GitHub API请求超时: {url}")
            except Exception as e:
                self.logger.error(f"请求异常: {str(e)}")
                raise

    async def get_repository_info(self, owner: str, repo: str) -> Repository:
        """获取仓库基本信息"""
        url = f"{self.base_url}/repos/{owner}/{repo}"
        data = await self._make_request(url)

        return Repository(
            name=data['name'],
            full_name=data['full_name'],
            description=data.get('description', ''),
            html_url=data['html_url'],
            language=data.get('language', ''),
            stars=data['stargazers_count'],
            forks=data['forks_count'],
            updated_at=datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00')),
            created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        )

    async def get_repository_updates(self, owner: str, repo: str, since: datetime) -> List[RepositoryUpdate]:
        """获取仓库更新信息"""
        # 获取最新的commits
        commits_url = f"{self.base_url}/repos/{owner}/{repo}/commits"
        params = {
            'since': since.isoformat(),
            'per_page': 100
        }

        commits_data = await self._make_request(commits_url, params)

        updates = []
        for commit in commits_data:
            updates.append(RepositoryUpdate(
                type='commit',
                title=commit['commit']['message'].split('\n')[0],
                description=commit['commit']['message'],
                author=commit['commit']['author']['name'],
                created_at=datetime.fromisoformat(commit['commit']['author']['date'].replace('Z', '+00:00')),
                html_url=commit['html_url']
            ))

        return updates

    async def get_issues(self, owner: str, repo: str, since: Optional[datetime] = None,
                        until: Optional[datetime] = None, state: str = "all",
                        per_page: int = 50, include_body: bool = False) -> List[Dict]:
        """获取仓库的 issues 列表"""
        url = f"{self.base_url}/repos/{owner}/{repo}/issues"
        params = {
            'state': state,
            'per_page': per_page,
            'sort': 'updated',
            'direction': 'desc'
        }

        if since:
            params['since'] = since.isoformat()

        data = await self._make_request(url, params)

        # 过滤掉 pull requests (GitHub API 中 issues 包含 pull requests)
        issues = []
        for item in data:
            if 'pull_request' not in item:
                # 时间过滤
                if until:
                    updated_at = datetime.fromisoformat(item['updated_at'].replace('Z', '+00:00'))
                    if updated_at > until:
                        continue

                issue_data = {
                    'number': item['number'],
                    'title': item['title'],
                    'state': item['state'],
                    'user': item['user']['login'],
                    'created_at': item['created_at'],
                    'updated_at': item['updated_at'],
                    'html_url': item['html_url'],
                    'labels': [label['name'] for label in item.get('labels', [])]
                }

                # 可选包含body内容
                if include_body and item.get('body'):
                    # 限制描述长度，减少token使用
                    body = item['body'][:150] + "..." if len(item['body']) > 150 else item['body']
                    issue_data['body'] = body

                issues.append(issue_data)

        return issues

    async def get_pull_requests(self, owner: str, repo: str, since: Optional[datetime] = None,
                               until: Optional[datetime] = None, state: str = "all",
                               per_page: int = 50, merged_only: bool = False,
                               include_body: bool = False) -> List[Dict]:
        """获取仓库的 pull requests 列表"""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
        params = {
            'state': state,
            'per_page': per_page,
            'sort': 'updated',
            'direction': 'desc'
        }

        data = await self._make_request(url, params)

        pull_requests = []
        for item in data:
            # 时间过滤
            if since:
                updated_at = datetime.fromisoformat(item['updated_at'].replace('Z', '+00:00'))
                if updated_at < since:
                    continue

            if until:
                updated_at = datetime.fromisoformat(item['updated_at'].replace('Z', '+00:00'))
                if updated_at > until:
                    continue

            # 如果只要merged的PR
            if merged_only and not item.get('merged_at'):
                continue

            pr_data = {
                'number': item['number'],
                'title': item['title'],
                'state': item['state'],
                'user': item['user']['login'],
                'created_at': item['created_at'],
                'updated_at': item['updated_at'],
                'html_url': item['html_url'],
                'merged_at': item.get('merged_at'),
                'draft': item.get('draft', False),
                'base_branch': item['base']['ref'],
                'head_branch': item['head']['ref']
            }

            # 可选包含body内容
            if include_body and item.get('body'):
                # 限制描述长度，减少token使用
                body = item['body'][:150] + "..." if len(item['body']) > 150 else item['body']
                pr_data['body'] = body

            pull_requests.append(pr_data)

        return pull_requests

    async def export_daily_progress(self, owner: str, repo: str,
                                   output_dir: str = "daily_progress",
                                   since: Optional[datetime] = None,
                                   until: Optional[datetime] = None,
                                   compact_mode: bool = True) -> str:
        """导出每日进展到 Markdown 文件"""
        # 默认时间范围：过去24小时
        if not since:
            since = datetime.now(timezone.utc) - timedelta(hours=24)
        if not until:
            until = datetime.now(timezone.utc)

        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # 根据模式调整参数
        if compact_mode:
            # 紧凑模式：只获取merged PR和open issues，不包含body
            issues = await self.get_issues(
                owner, repo, since=since, until=until,
                state="open", per_page=20, include_body=False
            )
            pull_requests = await self.get_pull_requests(
                owner, repo, since=since, until=until,
                per_page=20, merged_only=True, include_body=False
            )
        else:
            # 完整模式
            issues = await self.get_issues(
                owner, repo, since=since, until=until,
                per_page=50, include_body=True
            )
            pull_requests = await self.get_pull_requests(
                owner, repo, since=since, until=until,
                per_page=50, include_body=True
            )

        # 生成文件名
        date_str = until.strftime("%Y%m%d")
        filename = f"{repo}_{date_str}.md"
        filepath = output_path / filename

        # 生成 Markdown 内容
        markdown_content = self._generate_progress_markdown(
            repo, owner, issues, pull_requests, since, until, compact_mode
        )

        # 写入文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        self.logger.info(f"每日进展报告已导出到: {filepath}")
        return str(filepath)

    def _generate_progress_markdown(self, repo: str, owner: str, issues: List[Dict],
                                   pull_requests: List[Dict], since: datetime,
                                   until: datetime, compact_mode: bool = True) -> str:
        """生成进展 Markdown 内容"""
        date_range = f"{since.strftime('%Y-%m-%d %H:%M')} 至 {until.strftime('%Y-%m-%d %H:%M')}"

        content = f"""# {repo} 项目进展报告

## 📅 时间范围：{date_range}

"""

        # Pull Requests 部分（优先显示，因为更重要）
        if compact_mode:
            content += f"## ✅ 已合并 Pull Requests ({len(pull_requests)} 个)\n\n"
        else:
            content += f"## 🔄 Pull Requests 更新 ({len(pull_requests)} 个)\n\n"

        if pull_requests:
            for pr in pull_requests:
                content += f"### #{pr['number']} {pr['title']}\n"
                content += f"- **状态**: {pr['state']}"
                if pr['merged_at']:
                    merged_time = datetime.fromisoformat(pr['merged_at'].replace('Z', '+00:00'))
                    content += f" (已合并: {merged_time.strftime('%m-%d %H:%M')})"
                content += "\n"
                content += f"- **作者**: {pr['user']}\n"
                content += f"- **分支**: `{pr['head_branch']}` → `{pr['base_branch']}`\n"

                if not compact_mode:
                    content += f"- **链接**: [{pr['html_url']}]({pr['html_url']})\n"
                    if pr.get('body'):
                        content += f"- **描述**: {pr['body']}\n"
                content += "\n"
        else:
            content += "暂无相关 Pull Requests\n\n"

        # Issues 部分
        if compact_mode:
            content += f"## 🐛 待处理 Issues ({len(issues)} 个)\n\n"
        else:
            content += f"## 📋 Issues 更新 ({len(issues)} 个)\n\n"

        if issues:
            for issue in issues:
                content += f"### #{issue['number']} {issue['title']}\n"
                content += f"- **状态**: {issue['state']}\n"
                content += f"- **创建者**: {issue['user']}\n"

                if not compact_mode:
                    content += f"- **更新时间**: {issue['updated_at']}\n"
                    content += f"- **链接**: [{issue['html_url']}]({issue['html_url']})\n"

                if issue.get('labels'):
                    content += f"- **标签**: {', '.join(issue['labels'])}\n"

                if not compact_mode and issue.get('body'):
                    content += f"- **描述**: {issue['body']}\n"
                content += "\n"
        else:
            content += "暂无相关 Issues\n\n"

        # 统计信息
        content += f"""## 📊 统计摘要

- **时间范围**: {(until - since).total_seconds() / 3600:.1f} 小时
- **已合并 PR**: {len([pr for pr in pull_requests if pr.get('merged_at')])} 个
- **待处理 Issues**: {len([issue for issue in issues if issue['state'] == 'open'])} 个

---
*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*模式: {'紧凑模式' if compact_mode else '详细模式'}*
"""

        return content
