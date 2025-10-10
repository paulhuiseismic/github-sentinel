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


def parse_github_datetime(date_string: str) -> datetime:
    """解析GitHub API返回的时间字符串，确保返回timezone-aware的datetime"""
    if date_string.endswith('Z'):
        # GitHub API通常返回UTC时间，以'Z'结尾
        date_string = date_string.replace('Z', '+00:00')

    try:
        dt = datetime.fromisoformat(date_string)
        # 确保是timezone-aware的
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        # 如果解析失败，返回当前UTC时间
        return datetime.now(timezone.utc)


def ensure_utc_datetime(dt: datetime) -> datetime:
    """确保datetime是UTC时区的timezone-aware对象"""
    if dt is None:
        return None

    if dt.tzinfo is None:
        # 如果是naive datetime，假设它是UTC时间
        return dt.replace(tzinfo=timezone.utc)
    else:
        # 如果已经有时区信息，转换为UTC
        return dt.astimezone(timezone.utc)


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
        self.last_reset = datetime.now(timezone.utc)
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)

    async def _check_rate_limit(self):
        """检查API速率限制"""
        now = datetime.now(timezone.utc)
        if (now - self.last_reset).total_seconds() > 3600:
            self.requests_made = 0
            self.last_reset = now

        if self.requests_made >= self.rate_limit_per_hour:
            wait_time = 3600 - (now - self.last_reset).total_seconds()
            if wait_time > 0:
                self.logger.warning(f"达到速率限制，等待 {wait_time:.0f} 秒")
                await asyncio.sleep(wait_time)
                self.requests_made = 0
                self.last_reset = datetime.now(timezone.utc)

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
            updated_at=parse_github_datetime(data['updated_at']),
            created_at=parse_github_datetime(data['created_at'])
        )

    async def get_repository_updates(self, owner: str, repo: str, since: datetime) -> List[RepositoryUpdate]:
        """获取仓库更新信息"""
        # 确保since参数是timezone-aware的
        since = ensure_utc_datetime(since)

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
                created_at=parse_github_datetime(commit['commit']['author']['date']),
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
            since = ensure_utc_datetime(since)
            params['since'] = since.isoformat()

        data = await self._make_request(url, params)

        # 过滤掉 pull requests (GitHub API 中 issues 包含 pull requests)
        issues = []
        for item in data:
            if 'pull_request' not in item:
                # 时间过滤
                if until:
                    until = ensure_utc_datetime(until)
                    updated_at = parse_github_datetime(item['updated_at'])
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
                    'labels': [label['name'] for label in item['labels']]
                }

                if include_body:
                    issue_data['body'] = item.get('body', '')

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
            # 紧凑模式：只获取merged PR和closed issues，不包含body
            issues = await self.get_issues(
                owner, repo, since=since, until=until,
                state="closed", per_page=20, include_body=False
            )
            pull_requests = await self.get_pull_requests(
                owner, repo, since=since, until=until,
                per_page=20, merged_only=True, include_body=False
            )
        else:
            # 完整模式：获取所有状态的issues和PR
            issues = await self.get_issues(
                owner, repo, since=since, until=until,
                state="all", per_page=50, include_body=True
            )
            pull_requests = await self.get_pull_requests(
                owner, repo, since=since, until=until,
                state="all", per_page=50, merged_only=False, include_body=True
            )

        # 生成文件名
        date_str = until.strftime("%Y%m%d")
        filename = f"{repo}_{date_str}.md"
        filepath = output_path / filename

        # 生成 Markdown 内容
        content = self._generate_markdown_content(
            owner, repo, issues, pull_requests, since, until, compact_mode
        )

        # 写入文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        self.logger.info(f"每日进展报告已导出: {filepath}")
        return str(filepath)

    def _generate_markdown_content(self, owner: str, repo: str,
                                  issues: List[Dict], pull_requests: List[Dict],
                                  since: datetime, until: datetime,
                                  compact_mode: bool) -> str:
        """生成 Markdown 内容"""
        date_str = until.strftime("%Y-%m-%d")
        time_range = f"{since.strftime('%Y-%m-%d %H:%M')} 至 {until.strftime('%Y-%m-%d %H:%M')} (UTC)"
        mode_str = "紧凑模式" if compact_mode else "完整模式"

        content = f"""# {owner}/{repo} - 每日进展报告

**日期**: {date_str}  
**时间范围**: {time_range}  
**模式**: {mode_str}  
**生成时间**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC

---

## 📊 概览

- **Pull Requests**: {len(pull_requests)} 个{'已合并' if compact_mode else ''}
- **Issues**: {len(issues)} 个{'已关闭' if compact_mode else ''}

---

## 🔀 Pull Requests {f'(已合并)' if compact_mode else ''}

"""

        if pull_requests:
            for pr in pull_requests:
                status_icon = "✅" if pr.get('merged_at') else ("🔀" if pr['state'] == 'open' else "❌")
                merge_info = f" - 合并时间: {pr['merged_at']}" if pr.get('merged_at') else ""
                draft_info = " 📝" if pr.get('draft') else ""

                content += f"### {status_icon} #{pr['number']} {pr['title']}{draft_info}\n\n"
                content += f"- **作者**: {pr['user']}\n"
                content += f"- **状态**: {pr['state']}\n"
                content += f"- **分支**: {pr['head_branch']} → {pr['base_branch']}\n"
                content += f"- **创建时间**: {pr['created_at']}\n"
                if merge_info:
                    content += merge_info + "\n"
                content += f"- **链接**: [{pr['html_url']}]({pr['html_url']})\n"

                if not compact_mode and pr.get('body'):
                    content += f"- **描述**: {pr['body']}\n"

                content += "\n"
        else:
            content += f"无{'已合并' if compact_mode else ''}的 Pull Requests\n\n"

        content += f"""---

## 🐛 Issues {f'(已关闭)' if compact_mode else ''}

"""

        if issues:
            for issue in issues:
                status_icon = "✅" if issue['state'] == 'closed' else "🔴"
                labels_info = f" 🏷️ {', '.join(issue['labels'])}" if issue.get('labels') else ""

                content += f"### {status_icon} #{issue['number']} {issue['title']}{labels_info}\n\n"
                content += f"- **作者**: {issue['user']}\n"
                content += f"- **状态**: {issue['state']}\n"
                content += f"- **创建时间**: {issue['created_at']}\n"
                content += f"- **更新时间**: {issue['updated_at']}\n"
                content += f"- **链接**: [{issue['html_url']}]({issue['html_url']})\n"

                if not compact_mode and issue.get('body'):
                    content += f"- **描述**: {issue['body']}\n"

                content += "\n"
        else:
            content += f"无{'已关闭' if compact_mode else ''}的 Issues\n\n"

        content += """---

## 📈 统计信息

"""
        if compact_mode:
            content += f"- 已合并 PR: {len(pull_requests)}\n"
            content += f"- 已关闭 Issues: {len(issues)}\n"
        else:
            # 完整模式的统计
            merged_prs = len([pr for pr in pull_requests if pr.get('merged_at')])
            open_prs = len([pr for pr in pull_requests if pr['state'] == 'open'])
            closed_prs = len([pr for pr in pull_requests if pr['state'] == 'closed' and not pr.get('merged_at')])

            open_issues = len([issue for issue in issues if issue['state'] == 'open'])
            closed_issues = len([issue for issue in issues if issue['state'] == 'closed'])

            content += f"- 已合并 PR: {merged_prs}\n"
            content += f"- 开放 PR: {open_prs}\n"
            content += f"- 已关闭 PR: {closed_prs}\n"
            content += f"- 开放 Issues: {open_issues}\n"
            content += f"- 已关闭 Issues: {closed_issues}\n"

        content += f"\n**报告生成工具**: GitHub Sentinel v0.2\n"

        return content
