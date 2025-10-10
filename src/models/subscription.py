"""
订阅数据模型
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid


class NotificationType(Enum):
    """通知类型枚举"""
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    DISCORD = "discord"


class UpdateFrequency(Enum):
    """更新频率枚举"""
    DAILY = "daily"
    WEEKLY = "weekly"
    BOTH = "both"


class UpdateType(Enum):
    """更新类型枚举"""
    COMMITS = "commits"
    ISSUES = "issues"
    PULL_REQUESTS = "pull_requests"
    RELEASES = "releases"
    ALL = "all"


def utc_now():
    """获取UTC时间的datetime对象"""
    return datetime.now(timezone.utc)


def ensure_timezone_aware(dt: datetime) -> datetime:
    """确保datetime对象是timezone-aware的"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # 如果是naive datetime，假设它是UTC时间
        return dt.replace(tzinfo=timezone.utc)
    return dt


def ensure_timezone_naive(dt: datetime) -> datetime:
    """确保datetime对象是timezone-naive的"""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        # 如果是aware datetime，转换为UTC然后移除时区信息
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


@dataclass
class Subscription:
    """订阅模型"""
    repo_url: str
    owner: str
    repo_name: str
    notification_types: List[NotificationType]
    frequency: UpdateFrequency
    update_types: List[UpdateType] = field(default_factory=lambda: [UpdateType.ALL])
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_checked: Optional[datetime] = None
    is_active: bool = True
    filters: Optional[Dict[str, Any]] = None
    notification_config: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Subscription':
        """从字典创建订阅对象"""
        # 处理枚举类型转换
        notification_types = []
        for nt in data.get('notification_types', []):
            if isinstance(nt, str):
                notification_types.append(NotificationType(nt))
            else:
                notification_types.append(nt)

        frequency = data.get('frequency', 'daily')
        if isinstance(frequency, str):
            frequency = UpdateFrequency(frequency)

        update_types = []
        for ut in data.get('update_types', ['all']):
            if isinstance(ut, str):
                update_types.append(UpdateType(ut))
            else:
                update_types.append(ut)

        # 处理时间字段 - 确保时区一致性
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            try:
                # 尝试解析ISO格式时间
                created_at = datetime.fromisoformat(created_at)
                created_at = ensure_timezone_aware(created_at)
            except ValueError:
                created_at = datetime.now(timezone.utc)
        elif created_at is None:
            created_at = datetime.now(timezone.utc)
        else:
            created_at = ensure_timezone_aware(created_at)

        last_checked = data.get('last_checked')
        if isinstance(last_checked, str):
            try:
                last_checked = datetime.fromisoformat(last_checked)
                last_checked = ensure_timezone_aware(last_checked)
            except ValueError:
                last_checked = None
        elif last_checked is not None:
            last_checked = ensure_timezone_aware(last_checked)

        return cls(
            id=data.get('id', str(uuid.uuid4())),
            repo_url=data['repo_url'],
            owner=data['owner'],
            repo_name=data['repo_name'],
            notification_types=notification_types,
            frequency=frequency,
            update_types=update_types,
            created_at=created_at,
            last_checked=last_checked,
            is_active=data.get('is_active', True),
            filters=data.get('filters'),
            notification_config=data.get('notification_config')
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'repo_url': self.repo_url,
            'owner': self.owner,
            'repo_name': self.repo_name,
            'notification_types': [nt.value for nt in self.notification_types],
            'frequency': self.frequency.value,
            'update_types': [ut.value for ut in self.update_types],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_checked': self.last_checked.isoformat() if self.last_checked else None,
            'is_active': self.is_active,
            'filters': self.filters,
            'notification_config': self.notification_config
        }

    @staticmethod
    def parse_repo_url(repo_url: str) -> tuple[str, str]:
        """从仓库URL解析owner和repo_name"""
        if repo_url.startswith('https://github.com/'):
            parts = repo_url.replace('https://github.com/', '').strip('/').split('/')
            if len(parts) >= 2:
                return parts[0], parts[1]
        raise ValueError(f"Invalid GitHub repository URL: {repo_url}")

    @classmethod
    def create_from_url(cls, repo_url: str, **kwargs) -> 'Subscription':
        """从仓库URL创建订阅"""
        owner, repo_name = cls.parse_repo_url(repo_url)
        return cls(
            repo_url=repo_url,
            owner=owner,
            repo_name=repo_name,
            **kwargs
        )
