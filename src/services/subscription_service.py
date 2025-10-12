"""
订阅管理服务
"""
import json
import os
from datetime import datetime
from typing import List, Optional, Union
from pathlib import Path

from ..models.subscription import Subscription
from ..models.hackernews import HackerNewsSubscription
from ..config.settings import Settings


class SubscriptionService:
    """订阅管理服务"""

    def __init__(self, settings: Settings):
        self.settings = settings
        # GitHub订阅数据文件
        self.data_file = Path(settings.database.path)
        # Hacker News订阅数据文件
        self.hn_data_file = Path(settings.database.path).parent / "hackernews_subscriptions.json"
        self._ensure_data_files_exist()

    def _ensure_data_files_exist(self):
        """确保数据文件存在"""
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.data_file.exists():
            self._save_subscriptions([])
        if not self.hn_data_file.exists():
            self._save_hn_subscriptions([])

    def _load_subscriptions(self) -> List[Subscription]:
        """加载所有GitHub订阅"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [Subscription.from_dict(item) for item in data]
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"加载订阅失败: {e}")
            return []

    def _save_subscriptions(self, subscriptions: List[Subscription]):
        """保存所有GitHub订阅"""
        try:
            data = [sub.to_dict() for sub in subscriptions]
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存订阅失败: {e}")
            raise

    def _load_hn_subscriptions(self) -> List[HackerNewsSubscription]:
        """加载所有Hacker News订阅"""
        try:
            with open(self.hn_data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [HackerNewsSubscription.from_dict(item) for item in data]
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"加载Hacker News订阅失败: {e}")
            return []

    def _save_hn_subscriptions(self, subscriptions: List[HackerNewsSubscription]):
        """保存所有Hacker News订阅"""
        try:
            data = [sub.to_dict() for sub in subscriptions]
            with open(self.hn_data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存Hacker News订阅失败: {e}")
            raise

    async def get_all_subscriptions(self) -> List[Subscription]:
        """获取所有GitHub订阅"""
        return self._load_subscriptions()

    async def get_all_hn_subscriptions(self) -> List[HackerNewsSubscription]:
        """获取所有Hacker News订阅"""
        return self._load_hn_subscriptions()

    async def get_active_subscriptions(self) -> List[Subscription]:
        """获取活跃的GitHub订阅"""
        subscriptions = self._load_subscriptions()
        return [sub for sub in subscriptions if sub.is_active]

    async def get_active_hn_subscriptions(self) -> List[HackerNewsSubscription]:
        """获取活跃的Hacker News订阅"""
        subscriptions = self._load_hn_subscriptions()
        return [sub for sub in subscriptions if sub.enabled]

    async def get_subscription_by_id(self, subscription_id: str) -> Optional[Subscription]:
        """根据ID获取GitHub订阅"""
        subscriptions = self._load_subscriptions()
        for sub in subscriptions:
            if sub.id == subscription_id:
                return sub
        return None

    async def get_hn_subscription_by_id(self, subscription_id: str) -> Optional[HackerNewsSubscription]:
        """根据ID获取Hacker News订阅"""
        subscriptions = self._load_hn_subscriptions()
        for sub in subscriptions:
            if sub.id == subscription_id:
                return sub
        return None

    async def add_subscription(self, subscription: Subscription) -> bool:
        """添加新GitHub订阅"""
        try:
            subscriptions = self._load_subscriptions()

            # 检查是否已存在相同的仓库订阅
            for existing in subscriptions:
                if (existing.owner == subscription.owner and
                    existing.repo_name == subscription.repo_name and
                    existing.is_active):
                    print(f"仓库 {subscription.owner}/{subscription.repo_name} 已存在活跃订阅")
                    return False

            subscriptions.append(subscription)
            self._save_subscriptions(subscriptions)
            print(f"成功添加订阅: {subscription.owner}/{subscription.repo_name}")
            return True

        except Exception as e:
            print(f"添加订阅失败: {e}")
            return False

    async def add_hn_subscription(self, subscription: HackerNewsSubscription) -> bool:
        """添加新Hacker News订阅"""
        try:
            subscriptions = self._load_hn_subscriptions()

            # 检查是否已存在相同的订阅
            for existing in subscriptions:
                if existing.id == subscription.id and existing.enabled:
                    print(f"Hacker News订阅 {subscription.name} 已存在")
                    return False

            subscriptions.append(subscription)
            self._save_hn_subscriptions(subscriptions)
            print(f"成功添加Hacker News订阅: {subscription.name}")
            return True

        except Exception as e:
            print(f"添加Hacker News订阅失败: {e}")
            return False

    async def update_subscription(self, subscription: Subscription) -> bool:
        """更新GitHub订阅"""
        try:
            subscriptions = self._load_subscriptions()

            for i, existing in enumerate(subscriptions):
                if existing.id == subscription.id:
                    subscriptions[i] = subscription
                    self._save_subscriptions(subscriptions)
                    print(f"成功更新订阅: {subscription.owner}/{subscription.repo_name}")
                    return True

            print(f"未找到订阅ID: {subscription.id}")
            return False

        except Exception as e:
            print(f"更新订阅失败: {e}")
            return False

    async def update_hn_subscription(self, subscription: HackerNewsSubscription) -> bool:
        """更新Hacker News订阅"""
        try:
            subscriptions = self._load_hn_subscriptions()

            for i, existing in enumerate(subscriptions):
                if existing.id == subscription.id:
                    subscriptions[i] = subscription
                    self._save_hn_subscriptions(subscriptions)
                    print(f"成功更新Hacker News订阅: {subscription.name}")
                    return True

            print(f"未找到Hacker News订阅ID: {subscription.id}")
            return False

        except Exception as e:
            print(f"更新Hacker News订阅失败: {e}")
            return False

    async def deactivate_subscription(self, subscription_id: str) -> bool:
        """停用订阅"""
        try:
            subscriptions = self._load_subscriptions()

            for subscription in subscriptions:
                if subscription.id == subscription_id:
                    subscription.is_active = False
                    self._save_subscriptions(subscriptions)
                    print(f"成功停用订阅: {subscription.owner}/{subscription.repo_name}")
                    return True

            print(f"未找到订阅ID: {subscription_id}")
            return False

        except Exception as e:
            print(f"停用订阅失败: {e}")
            return False

    async def remove_subscription(self, subscription_id: str) -> bool:
        """删除GitHub订阅"""
        try:
            subscriptions = self._load_subscriptions()
            original_count = len(subscriptions)

            subscriptions = [sub for sub in subscriptions if sub.id != subscription_id]

            if len(subscriptions) < original_count:
                self._save_subscriptions(subscriptions)
                print(f"成功删除订阅ID: {subscription_id}")
                return True
            else:
                print(f"未找到订阅ID: {subscription_id}")
                return False

        except Exception as e:
            print(f"删除订阅失败: {e}")
            return False

    async def remove_hn_subscription(self, subscription_id: str) -> bool:
        """删除Hacker News订阅"""
        try:
            subscriptions = self._load_hn_subscriptions()

            for subscription in subscriptions:
                if subscription.id == subscription_id:
                    subscription.enabled = False
                    self._save_hn_subscriptions(subscriptions)
                    print(f"成功删除Hacker News订阅: {subscription.name}")
                    return True

            print(f"未找到Hacker News订阅ID: {subscription_id}")
            return False

        except Exception as e:
            print(f"删除Hacker News订阅失败: {e}")
            return False

    async def update_last_checked(self, subscription_ids: List[str]) -> bool:
        """更新最后检查时间"""
        try:
            subscriptions = self._load_subscriptions()
            updated = False
            now = datetime.now()

            for subscription in subscriptions:
                if subscription.id in subscription_ids:
                    subscription.last_checked = now
                    updated = True

            if updated:
                self._save_subscriptions(subscriptions)
                print(f"成功更新 {len(subscription_ids)} 个订阅的检查时间")
                return True
            else:
                print("没有找到需要更新的订阅")
                return False

        except Exception as e:
            print(f"更新检查时间失败: {e}")
            return False

    async def get_subscriptions_by_frequency(self, frequency: str) -> List[Subscription]:
        """根据频率获取订阅"""
        subscriptions = await self.get_active_subscriptions()
        return [sub for sub in subscriptions if sub.frequency.value == frequency or sub.frequency.value == 'both']

    async def get_subscription_stats(self) -> dict:
        """获取订阅统计信息"""
        subscriptions = self._load_subscriptions()
        active_subs = [sub for sub in subscriptions if sub.is_active]

        frequency_stats = {}
        notification_stats = {}

        for sub in active_subs:
            # 统计频率
            freq = sub.frequency.value
            frequency_stats[freq] = frequency_stats.get(freq, 0) + 1

            # 统计通知类型
            for nt in sub.notification_types:
                notification_stats[nt.value] = notification_stats.get(nt.value, 0) + 1

        return {
            'total_subscriptions': len(subscriptions),
            'active_subscriptions': len(active_subs),
            'inactive_subscriptions': len(subscriptions) - len(active_subs),
            'frequency_distribution': frequency_stats,
            'notification_type_distribution': notification_stats
        }
