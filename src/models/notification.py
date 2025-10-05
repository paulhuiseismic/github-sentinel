"""
通知数据模型
"""
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from enum import Enum


class NotificationChannel(Enum):
    """通知渠道枚举"""
    EMAIL = "email"
    SLACK = "slack"
    DISCORD = "discord"
    WEBHOOK = "webhook"


@dataclass
class NotificationPayload:
    """通知载荷"""
    channel: NotificationChannel
    subject: str
    body: str
    metadata: Dict[str, Any]
    recipients: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'channel': self.channel.value,
            'subject': self.subject,
            'body': self.body,
            'metadata': self.metadata,
            'recipients': self.recipients
        }

    @classmethod
    def create_email(cls, subject: str, body: str, recipients: List[str], **metadata) -> 'NotificationPayload':
        """创建邮件通知"""
        return cls(
            channel=NotificationChannel.EMAIL,
            subject=subject,
            body=body,
            recipients=recipients,
            metadata=metadata
        )

    @classmethod
    def create_slack(cls, subject: str, body: str, **metadata) -> 'NotificationPayload':
        """创建Slack通知"""
        return cls(
            channel=NotificationChannel.SLACK,
            subject=subject,
            body=body,
            metadata=metadata
        )

    @classmethod
    def create_discord(cls, subject: str, body: str, **metadata) -> 'NotificationPayload':
        """创建Discord通知"""
        return cls(
            channel=NotificationChannel.DISCORD,
            subject=subject,
            body=body,
            metadata=metadata
        )

    @classmethod
    def create_webhook(cls, subject: str, body: str, webhook_url: str, **metadata) -> 'NotificationPayload':
        """创建Webhook通知"""
        metadata['webhook_url'] = webhook_url
        return cls(
            channel=NotificationChannel.WEBHOOK,
            subject=subject,
            body=body,
            metadata=metadata
        )
