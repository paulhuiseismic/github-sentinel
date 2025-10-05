"""
测试服务层
"""
import unittest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.subscription import Subscription, NotificationType, UpdateFrequency, UpdateType
from src.models.repository import RepositoryUpdate
from src.services.subscription_service import SubscriptionService
from src.services.github_service import GitHubService
from src.services.update_service import UpdateService
from src.config.settings import Settings, GitHubConfig, NotificationConfig, DatabaseConfig


class TestSubscriptionService(unittest.TestCase):
    """测试订阅服务"""

    def setUp(self):
        """设置测试环境"""
        self.settings = Settings(
            github=GitHubConfig(token="test_token"),
            notification=NotificationConfig(),
            database=DatabaseConfig(path="test_subscriptions.json")
        )
        self.service = SubscriptionService(self.settings)

    def test_create_subscription(self):
        """测试创建订阅"""
        subscription = Subscription.create_from_url(
            repo_url="https://github.com/owner/repo",
            notification_types=[NotificationType.EMAIL],
            frequency=UpdateFrequency.DAILY
        )

        self.assertEqual(subscription.owner, "owner")
        self.assertEqual(subscription.repo_name, "repo")
        self.assertEqual(subscription.frequency, UpdateFrequency.DAILY)

    def test_parse_repo_url(self):
        """测试仓库URL解析"""
        owner, repo = Subscription.parse_repo_url("https://github.com/owner/repo")
        self.assertEqual(owner, "owner")
        self.assertEqual(repo, "repo")

        with self.assertRaises(ValueError):
            Subscription.parse_repo_url("invalid_url")


class TestGitHubService(unittest.TestCase):
    """测试GitHub服务"""

    def setUp(self):
        """设置测试环境"""
        self.service = GitHubService("test_token")

    @patch('aiohttp.ClientSession.get')
    async def test_get_repository_info(self, mock_get):
        """测试获取仓库信息"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "id": 123,
            "name": "test-repo",
            "full_name": "owner/test-repo",
            "owner": {"login": "owner"},
            "description": "Test repository",
            "html_url": "https://github.com/owner/test-repo",
            "stargazers_count": 10,
            "forks_count": 5
        }
        mock_get.return_value.__aenter__.return_value = mock_response

        repo = await self.service.get_repository_info("owner", "test-repo")
        self.assertEqual(repo.name, "test-repo")
        self.assertEqual(repo.owner, "owner")


class TestUpdateService(unittest.TestCase):
    """测试更新服务"""

    def setUp(self):
        """设置测试环境"""
        self.settings = Settings(
            github=GitHubConfig(token="test_token"),
            notification=NotificationConfig(),
            database=DatabaseConfig()
        )
        self.service = UpdateService(self.settings)

    def test_apply_filters(self):
        """测试过滤器应用"""
        updates = [
            RepositoryUpdate(
                repo_name="test",
                owner="owner",
                update_type="commits",
                title="Fix bug",
                description=None,
                url="https://github.com/owner/test/commit/123",
                author="user1",
                created_at=datetime.now()
            ),
            RepositoryUpdate(
                repo_name="test",
                owner="owner",
                update_type="issues",
                title="Feature request",
                description=None,
                url="https://github.com/owner/test/issues/1",
                author="user2",
                created_at=datetime.now()
            )
        ]

        # 测试作者过滤器
        filters = {"authors": ["user1"]}
        filtered = self.service._apply_filters(updates, filters)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].author, "user1")


if __name__ == '__main__':
    unittest.main()
