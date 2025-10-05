"""
测试数据模型
"""
import unittest
from datetime import datetime
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.subscription import Subscription, NotificationType, UpdateFrequency, UpdateType
from src.models.repository import RepositoryUpdate, Repository
from src.models.report import Report


class TestSubscriptionModel(unittest.TestCase):
    """测试订阅模型"""

    def test_subscription_creation(self):
        """测试订阅创建"""
        sub = Subscription(
            repo_url="https://github.com/owner/repo",
            owner="owner",
            repo_name="repo",
            notification_types=[NotificationType.EMAIL],
            frequency=UpdateFrequency.DAILY
        )

        self.assertEqual(sub.owner, "owner")
        self.assertEqual(sub.repo_name, "repo")
        self.assertTrue(sub.is_active)

    def test_subscription_serialization(self):
        """测试订阅序列化"""
        sub = Subscription(
            repo_url="https://github.com/owner/repo",
            owner="owner",
            repo_name="repo",
            notification_types=[NotificationType.EMAIL, NotificationType.SLACK],
            frequency=UpdateFrequency.WEEKLY
        )

        data = sub.to_dict()
        self.assertIn('id', data)
        self.assertEqual(data['owner'], 'owner')
        self.assertEqual(data['notification_types'], ['email', 'slack'])

        # 测试反序列化
        restored = Subscription.from_dict(data)
        self.assertEqual(restored.owner, sub.owner)
        self.assertEqual(restored.frequency, sub.frequency)


class TestRepositoryModel(unittest.TestCase):
    """测试仓库模型"""

    def test_repository_update_creation(self):
        """测试仓库更新创建"""
        update = RepositoryUpdate(
            repo_name="test-repo",
            owner="test-owner",
            update_type="commits",
            title="Test commit",
            description="Test description",
            url="https://github.com/test-owner/test-repo/commit/123",
            author="test-user",
            created_at=datetime.now()
        )

        self.assertEqual(update.repo_name, "test-repo")
        self.assertEqual(update.update_type, "commits")


class TestReportModel(unittest.TestCase):
    """测试报告模型"""

    def test_report_generation(self):
        """测试报告生成"""
        updates = [
            RepositoryUpdate(
                repo_name="repo1",
                owner="owner1",
                update_type="commits",
                title="Commit 1",
                description=None,
                url="https://github.com/owner1/repo1/commit/1",
                author="user1",
                created_at=datetime.now()
            ),
            RepositoryUpdate(
                repo_name="repo2",
                owner="owner2",
                update_type="issues",
                title="Issue 1",
                description=None,
                url="https://github.com/owner2/repo2/issues/1",
                author="user2",
                created_at=datetime.now()
            )
        ]

        report = Report(report_type="daily", updates=updates)
        summary = report.generate_summary()

        self.assertEqual(summary['total_updates'], 2)
        self.assertEqual(summary['repositories_count'], 2)
        self.assertIn('commits', summary['update_types'])
        self.assertIn('issues', summary['update_types'])

    def test_report_text_format(self):
        """测试报告文本格式"""
        report = Report(report_type="daily", updates=[])
        text = report.to_text()
        self.assertIn("暂无更新", text)


if __name__ == '__main__':
    unittest.main()
