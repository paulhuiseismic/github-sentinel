"""
Hacker News 数据模型
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
import json


@dataclass
class HackerNewsItem:
    """Hacker News 项目模型"""
    id: int
    title: str
    url: str = ""
    score: int = 0
    by: str = ""
    time: datetime = field(default_factory=datetime.now)
    descendants: int = 0  # 评论数
    type: str = "story"
    text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'url': self.url,
            'score': self.score,
            'by': self.by,
            'time': self.time.isoformat(),
            'descendants': self.descendants,
            'type': self.type,
            'text': self.text
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HackerNewsItem':
        """从字典创建实例"""
        if isinstance(data['time'], str):
            data['time'] = datetime.fromisoformat(data['time'])
        return cls(**data)

    def __str__(self) -> str:
        return f"HackerNewsItem(id={self.id}, title='{self.title[:50]}...', score={self.score})"


@dataclass
class HackerNewsUpdate:
    """Hacker News 更新信息"""
    timestamp: datetime
    new_stories: List[HackerNewsItem] = field(default_factory=list)
    total_stories: int = 0
    new_stories_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'new_stories': [story.to_dict() for story in self.new_stories],
            'total_stories': self.total_stories,
            'new_stories_count': self.new_stories_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HackerNewsUpdate':
        """从字典创建实例"""
        if isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])

        new_stories = []
        for story_data in data.get('new_stories', []):
            new_stories.append(HackerNewsItem.from_dict(story_data))

        return cls(
            timestamp=data['timestamp'],
            new_stories=new_stories,
            total_stories=data.get('total_stories', 0),
            new_stories_count=data.get('new_stories_count', 0)
        )

    def __str__(self) -> str:
        return f"HackerNewsUpdate(timestamp={self.timestamp}, new_stories={self.new_stories_count})"


@dataclass
class HackerNewsSubscription:
    """Hacker News 订阅模型"""
    id: str = "hackernews_top"  # 固定ID，因为只监控热门话题
    name: str = "Hacker News 热门话题"
    frequency: str = "hourly"  # 每小时检查一次
    enabled: bool = True
    last_check: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    limit: int = 30  # 获取前30个热门故事

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'frequency': self.frequency,
            'enabled': self.enabled,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'created_at': self.created_at.isoformat(),
            'limit': self.limit
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HackerNewsSubscription':
        """从字典创建实例"""
        if data.get('last_check'):
            data['last_check'] = datetime.fromisoformat(data['last_check'])
        if isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)

    def __str__(self) -> str:
        return f"HackerNewsSubscription(name='{self.name}', frequency={self.frequency})"
