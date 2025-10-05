"""
GitHub API 服务
"""
import aiohttp
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

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

                    # 处理速率限制响应头
                    if 'X-RateLimit-Remaining' in response.headers:
                        remaining = int(response.headers['X-RateLimit-Remaining'])
                        if remaining < 100:
                            self.logger.warning(f"API速率限制剩余: {remaining}")

                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        raise ValueError(f"仓库不存在或无权限访问: {url}")
                    elif response.status == 403:
                        error_msg = "API访问被拒绝"
                        if 'X-RateLimit-Remaining' in response.headers:
                            remaining = int(response.headers['X-RateLimit-Remaining'])
                            if remaining == 0:
                                reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                                error_msg += f"，速率限制已达上限，重置时间: {datetime.fromtimestamp(reset_time)}"
                        raise ValueError(error_msg)
                    elif response.status == 401:
                        raise ValueError("GitHub token无效或已过期")
                    else:
                        response.raise_for_status()

            except aiohttp.ClientError as e:
                self.logger.error(f"网络请求错误: {e}")
                raise
            except asyncio.TimeoutError:
                self.logger.error(f"请求超时: {url}")
                raise

    async def get_repository_info(self, owner: str, repo: str) -> Repository:
        """获取仓库基本信息"""
        url = f"{self.base_url}/repos/{owner}/{repo}"
        data = await self._make_request(url)
        return Repository.from_dict(data)

    async def get_recent_commits(self, owner: str, repo: str, since: datetime, per_page: int = 100) -> List[RepositoryUpdate]:
        """获取最近提交"""
        url = f"{self.base_url}/repos/{owner}/{repo}/commits"
        params = {
            "since": since.isoformat(),
            "per_page": min(per_page, 100)  # GitHub API限制最大100
        }

        try:
            commits_data = await self._make_request(url, params)
            updates = []

            for commit_data in commits_data:
                try:
                    update = RepositoryUpdate.from_commit(owner, repo, commit_data)
                    updates.append(update)
                except Exception as e:
                    self.logger.warning(f"解析commit失败: {e}")
                    continue

            return updates

        except Exception as e:
            self.logger.error(f"获取commits失败 {owner}/{repo}: {e}")
            return []

    async def get_recent_issues(self, owner: str, repo: str, since: datetime, state: str = "all") -> List[RepositoryUpdate]:
        """获取最近问题"""
        url = f"{self.base_url}/repos/{owner}/{repo}/issues"
        params = {
            "since": since.isoformat(),
            "state": state,
            "per_page": 100
        }

        try:
            issues_data = await self._make_request(url, params)
            updates = []

            for issue_data in issues_data:
                # 跳过PR（GitHub API中issues包含PR）
                if issue_data.get("pull_request"):
                    continue

                try:
                    update = RepositoryUpdate.from_issue(owner, repo, issue_data)
                    updates.append(update)
                except Exception as e:
                    self.logger.warning(f"解析issue失败: {e}")
                    continue

            return updates

        except Exception as e:
            self.logger.error(f"获取issues失败 {owner}/{repo}: {e}")
            return []

    async def get_recent_pull_requests(self, owner: str, repo: str, since: datetime, state: str = "all") -> List[RepositoryUpdate]:
        """获取最近拉取请求"""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
        params = {
            "state": state,
            "sort": "updated",
            "direction": "desc",
            "per_page": 100
        }

        try:
            prs_data = await self._make_request(url, params)
            updates = []

            for pr_data in prs_data:
                # 检查更新时间
                updated_at = datetime.fromisoformat(pr_data['updated_at'].replace('Z', '+00:00'))
                if updated_at < since:
                    break  # 由于按更新时间排序，可以提前退出

                try:
                    update = RepositoryUpdate.from_pull_request(owner, repo, pr_data)
                    updates.append(update)
                except Exception as e:
                    self.logger.warning(f"解析PR失败: {e}")
                    continue

            return updates

        except Exception as e:
            self.logger.error(f"获取PRs失败 {owner}/{repo}: {e}")
            return []

    async def get_recent_releases(self, owner: str, repo: str, since: datetime, per_page: int = 10) -> List[RepositoryUpdate]:
        """获取最近发布"""
        url = f"{self.base_url}/repos/{owner}/{repo}/releases"
        params = {"per_page": min(per_page, 100)}

        try:
            releases_data = await self._make_request(url, params)
            updates = []

            for release_data in releases_data:
                # 检查发布时间
                created_at = datetime.fromisoformat(release_data['created_at'].replace('Z', '+00:00'))
                if created_at < since:
                    break  # 由于GitHub按时间排序，可以提前退出

                try:
                    update = RepositoryUpdate.from_release(owner, repo, release_data)
                    updates.append(update)
                except Exception as e:
                    self.logger.warning(f"解析release失败: {e}")
                    continue

            return updates

        except Exception as e:
            self.logger.error(f"获取releases失败 {owner}/{repo}: {e}")
            return []

    async def validate_repository(self, owner: str, repo: str) -> bool:
        """验证仓库是否存在且可访问"""
        try:
            await self.get_repository_info(owner, repo)
            return True
        except Exception:
            return False

    async def get_rate_limit_status(self) -> Dict[str, int]:
        """获取API速率限制状态"""
        url = f"{self.base_url}/rate_limit"
        try:
            data = await self._make_request(url)
            return data.get("rate", {})
        except Exception as e:
            self.logger.error(f"获取速率限制状态失败: {e}")
            return {}
