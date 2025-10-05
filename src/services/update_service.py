"""
更新获取服务
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

from ..models.subscription import Subscription, UpdateType
from ..models.repository import RepositoryUpdate
from ..services.github_service import GitHubService
from ..config.settings import Settings


class UpdateService:
    """更新获取服务"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.github_service = GitHubService(
            token=settings.github.token,
            rate_limit_per_hour=settings.github.rate_limit_per_hour,
            timeout=settings.github.timeout
        )
        self.logger = logging.getLogger(__name__)

    async def fetch_updates(self, subscriptions: List[Subscription], days: int = 1) -> List[RepositoryUpdate]:
        """获取订阅的更新"""
        if not subscriptions:
            return []

        since = datetime.now() - timedelta(days=days)
        all_updates = []

        # 使用信号量控制并发请求数
        semaphore = asyncio.Semaphore(self.settings.max_concurrent_requests)

        async def fetch_repo_updates(sub: Subscription) -> List[RepositoryUpdate]:
            """获取单个仓库的更新"""
            async with semaphore:
                try:
                    return await self._fetch_single_repo_updates(sub, since)
                except Exception as e:
                    self.logger.error(f"获取仓库更新失败 {sub.owner}/{sub.repo_name}: {e}")
                    return []

        # 并发获取所有订阅的更新
        tasks = [fetch_repo_updates(sub) for sub in subscriptions]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 合并结果
        for result in results:
            if isinstance(result, list):
                all_updates.extend(result)
            elif isinstance(result, Exception):
                self.logger.error(f"获取更新时出现异常: {result}")

        # 按时间排序
        all_updates.sort(key=lambda x: x.created_at, reverse=True)

        self.logger.info(f"共获取到 {len(all_updates)} 个更新")
        return all_updates

    async def _fetch_single_repo_updates(self, subscription: Subscription, since: datetime) -> List[RepositoryUpdate]:
        """获取单个仓库的更新"""
        updates = []
        owner = subscription.owner
        repo = subscription.repo_name

        # 使用订阅的最后检查时间或传入的since时间
        effective_since = subscription.last_checked or since

        try:
            # 根据订阅的更新类型获取不同类型的更新
            update_types = subscription.update_types

            if UpdateType.ALL in update_types:
                # 获取所有类型的更新
                commits = await self.github_service.get_recent_commits(owner, repo, effective_since)
                issues = await self.github_service.get_recent_issues(owner, repo, effective_since)
                prs = await self.github_service.get_recent_pull_requests(owner, repo, effective_since)
                releases = await self.github_service.get_recent_releases(owner, repo, effective_since)

                updates.extend(commits)
                updates.extend(issues)
                updates.extend(prs)
                updates.extend(releases)

            else:
                # 根据指定的类型获取更新
                if UpdateType.COMMITS in update_types:
                    commits = await self.github_service.get_recent_commits(owner, repo, effective_since)
                    updates.extend(commits)

                if UpdateType.ISSUES in update_types:
                    issues = await self.github_service.get_recent_issues(owner, repo, effective_since)
                    updates.extend(issues)

                if UpdateType.PULL_REQUESTS in update_types:
                    prs = await self.github_service.get_recent_pull_requests(owner, repo, effective_since)
                    updates.extend(prs)

                if UpdateType.RELEASES in update_types:
                    releases = await self.github_service.get_recent_releases(owner, repo, effective_since)
                    updates.extend(releases)

            # 应用过滤器
            if subscription.filters:
                updates = self._apply_filters(updates, subscription.filters)

            self.logger.info(f"仓库 {owner}/{repo} 获取到 {len(updates)} 个更新")
            return updates

        except Exception as e:
            self.logger.error(f"获取仓库 {owner}/{repo} 更新失败: {e}")
            return []

    def _apply_filters(self, updates: List[RepositoryUpdate], filters: Dict[str, Any]) -> List[RepositoryUpdate]:
        """应用过滤器"""
        filtered_updates = updates

        try:
            # 作者过滤器
            if 'authors' in filters and filters['authors']:
                allowed_authors = set(filters['authors'])
                filtered_updates = [u for u in filtered_updates if u.author in allowed_authors]

            # 排除作者过滤器
            if 'exclude_authors' in filters and filters['exclude_authors']:
                excluded_authors = set(filters['exclude_authors'])
                filtered_updates = [u for u in filtered_updates if u.author not in excluded_authors]

            # 关键词过滤器
            if 'keywords' in filters and filters['keywords']:
                keywords = [kw.lower() for kw in filters['keywords']]
                filtered_updates = [
                    u for u in filtered_updates
                    if any(kw in u.title.lower() or (u.description and kw in u.description.lower())
                           for kw in keywords)
                ]

            # 排除关键词过滤器
            if 'exclude_keywords' in filters and filters['exclude_keywords']:
                exclude_keywords = [kw.lower() for kw in filters['exclude_keywords']]
                filtered_updates = [
                    u for u in filtered_updates
                    if not any(kw in u.title.lower() or (u.description and kw in u.description.lower())
                              for kw in exclude_keywords)
                ]

            # 更新类型过滤器
            if 'update_types' in filters and filters['update_types']:
                allowed_types = set(filters['update_types'])
                filtered_updates = [u for u in filtered_updates if u.update_type in allowed_types]

            self.logger.debug(f"过滤器应用完成，从 {len(updates)} 个更新过滤到 {len(filtered_updates)} 个")

        except Exception as e:
            self.logger.error(f"应用过滤器失败: {e}")
            return updates

        return filtered_updates

    async def validate_subscription(self, subscription: Subscription) -> bool:
        """验证订阅的仓库是否有效"""
        try:
            return await self.github_service.validate_repository(subscription.owner, subscription.repo_name)
        except Exception as e:
            self.logger.error(f"验证仓库失败 {subscription.owner}/{subscription.repo_name}: {e}")
            return False

    async def get_repository_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """获取仓库信息"""
        try:
            repo_info = await self.github_service.get_repository_info(owner, repo)
            return {
                'name': repo_info.name,
                'full_name': repo_info.full_name,
                'description': repo_info.description,
                'stars': repo_info.stargazers_count,
                'forks': repo_info.forks_count,
                'language': repo_info.language,
                'url': repo_info.html_url
            }
        except Exception as e:
            self.logger.error(f"获取仓库信息失败 {owner}/{repo}: {e}")
            return {}

    async def get_api_rate_limit_status(self) -> Dict[str, Any]:
        """获取API速率限制状态"""
        try:
            return await self.github_service.get_rate_limit_status()
        except Exception as e:
            self.logger.error(f"获取API速率限制状态失败: {e}")
            return {}
