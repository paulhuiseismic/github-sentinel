"""
通知服务
"""
import aiohttp
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
import logging
import json

from ..models.subscription import Subscription, NotificationType
from ..models.report import Report
from ..models.notification import NotificationPayload, NotificationChannel
from ..config.settings import Settings


class NotificationService:
    """通知服务"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)

    async def send_notifications(self, report: Report, subscriptions: List[Subscription]):
        """发送通知"""
        if not report.updates:
            self.logger.info("没有更新内容，跳过通知发送")
            return

        # 按通知类型分组订阅
        notification_groups = self._group_subscriptions_by_notification_type(subscriptions)

        # 并发发送不同类型的通知
        tasks = []

        if NotificationType.EMAIL in notification_groups:
            tasks.append(self._send_email_notifications(report, notification_groups[NotificationType.EMAIL]))

        if NotificationType.SLACK in notification_groups:
            tasks.append(self._send_slack_notifications(report, notification_groups[NotificationType.SLACK]))

        if NotificationType.DISCORD in notification_groups:
            tasks.append(self._send_discord_notifications(report, notification_groups[NotificationType.DISCORD]))

        if NotificationType.WEBHOOK in notification_groups:
            tasks.append(self._send_webhook_notifications(report, notification_groups[NotificationType.WEBHOOK]))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def _group_subscriptions_by_notification_type(self, subscriptions: List[Subscription]) -> Dict[NotificationType, List[Subscription]]:
        """按通知类型分组订阅"""
        groups = {}

        for subscription in subscriptions:
            for notification_type in subscription.notification_types:
                if notification_type not in groups:
                    groups[notification_type] = []
                groups[notification_type].append(subscription)

        return groups

    async def _send_email_notifications(self, report: Report, subscriptions: List[Subscription]):
        """发送邮件通知"""
        if not self.settings.notification.email_smtp_server:
            self.logger.warning("邮件SMTP服务器未配置，跳过邮件通知")
            return

        try:
            # 收集邮件接收者
            recipients = set()
            for sub in subscriptions:
                if sub.notification_config and 'email_recipients' in sub.notification_config:
                    recipients.update(sub.notification_config['email_recipients'])

            if not recipients:
                self.logger.warning("没有配置邮件接收者")
                return

            # 创建邮件内容
            subject = f"GitHub Sentinel {report.report_type.upper()} 报告 - {report.generated_at.strftime('%Y-%m-%d')}"
            html_body = report.to_html()
            text_body = report.to_text()

            # 发送邮件
            await self._send_email(list(recipients), subject, text_body, html_body)
            self.logger.info(f"邮件通知发送成功，接收者: {len(recipients)} 人")

        except Exception as e:
            self.logger.error(f"发送邮件通知失败: {e}")

    async def _send_email(self, recipients: List[str], subject: str, text_body: str, html_body: str):
        """发送邮件"""
        smtp_server = self.settings.notification.email_smtp_server
        smtp_port = self.settings.notification.email_port
        username = self.settings.notification.email_username
        password = self.settings.notification.email_password
        use_tls = self.settings.notification.email_use_tls

        if not all([smtp_server, username, password]):
            raise ValueError("邮件配置不完整")

        # 创建邮件
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = username
        msg['To'] = ', '.join(recipients)

        # 添加文本和HTML部分
        text_part = MIMEText(text_body, 'plain', 'utf-8')
        html_part = MIMEText(html_body, 'html', 'utf-8')

        msg.attach(text_part)
        msg.attach(html_part)

        # 发送邮件
        def send_email_sync():
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                if use_tls:
                    server.starttls()
                server.login(username, password)
                server.send_message(msg)

        # 在线程中执行同步邮件发送
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, send_email_sync)

    async def _send_slack_notifications(self, report: Report, subscriptions: List[Subscription]):
        """发送Slack通知"""
        webhook_url = self.settings.notification.slack_webhook_url
        if not webhook_url:
            self.logger.warning("Slack Webhook URL未配置，跳过Slack通知")
            return

        try:
            # 创建Slack消息格式
            slack_message = self._format_slack_message(report)

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=slack_message,
                    timeout=aiohttp.ClientTimeout(total=self.settings.notification.webhook_timeout)
                ) as response:
                    if response.status == 200:
                        self.logger.info("Slack通知发送成功")
                    else:
                        self.logger.error(f"Slack通知发送失败: {response.status}")

        except Exception as e:
            self.logger.error(f"发送Slack通知失败: {e}")

    def _format_slack_message(self, report: Report) -> Dict[str, Any]:
        """格式化Slack消息"""
        summary = report.summary or report.generate_summary()

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📊 GitHub Sentinel {report.report_type.upper()} 报告"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*生成时间:* {report.generated_at.strftime('%Y-%m-%d %H:%M')}\n*总更新数:* {summary['total_updates']}\n*涉及仓库:* {summary['repositories_count']}"
                }
            }
        ]

        # 添加更新类型统计
        if summary['update_types']:
            type_text = "\n".join([f"• {type_name}: {count}" for type_name, count in summary['update_types'].items()])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*更新类型分布:*\n{type_text}"
                }
            })

        # 添加活跃贡献者
        if summary['top_contributors']:
            contributor_text = "\n".join([f"• {c['author']}: {c['count']} 次贡献" for c in summary['top_contributors'][:5]])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*活跃贡献者:*\n{contributor_text}"
                }
            })

        return {"blocks": blocks}

    async def _send_discord_notifications(self, report: Report, subscriptions: List[Subscription]):
        """发送Discord通知"""
        webhook_url = self.settings.notification.discord_webhook_url
        if not webhook_url:
            self.logger.warning("Discord Webhook URL未配置，跳过Discord通知")
            return

        try:
            # 创建Discord消息格式
            discord_message = self._format_discord_message(report)

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=discord_message,
                    timeout=aiohttp.ClientTimeout(total=self.settings.notification.webhook_timeout)
                ) as response:
                    if response.status == 204:  # Discord返回204表示成功
                        self.logger.info("Discord通知发送成功")
                    else:
                        self.logger.error(f"Discord通知发送失败: {response.status}")

        except Exception as e:
            self.logger.error(f"发送Discord通知失败: {e}")

    def _format_discord_message(self, report: Report) -> Dict[str, Any]:
        """格式化Discord消息"""
        summary = report.summary or report.generate_summary()

        embed = {
            "title": f"📊 GitHub Sentinel {report.report_type.upper()} 报告",
            "description": f"生成时间: {report.generated_at.strftime('%Y-%m-%d %H:%M')}",
            "color": 0x1f8b4c,  # 绿色
            "fields": [
                {
                    "name": "📈 统计摘要",
                    "value": f"总更新数: {summary['total_updates']}\n涉及仓库: {summary['repositories_count']}",
                    "inline": True
                }
            ]
        }

        # 添加更新类型统计
        if summary['update_types']:
            type_text = "\n".join([f"{type_name}: {count}" for type_name, count in summary['update_types'].items()])
            embed["fields"].append({
                "name": "📋 更新类型分布",
                "value": type_text,
                "inline": True
            })

        # 添加活跃贡献者
        if summary['top_contributors']:
            contributor_text = "\n".join([f"{c['author']}: {c['count']} 次" for c in summary['top_contributors'][:5]])
            embed["fields"].append({
                "name": "👥 活跃贡献者",
                "value": contributor_text,
                "inline": False
            })

        return {"embeds": [embed]}

    async def _send_webhook_notifications(self, report: Report, subscriptions: List[Subscription]):
        """发送Webhook通知"""
        try:
            # 收集所有webhook URL
            webhook_urls = set()
            for sub in subscriptions:
                if sub.notification_config and 'webhook_url' in sub.notification_config:
                    webhook_urls.add(sub.notification_config['webhook_url'])

            if not webhook_urls:
                self.logger.warning("没有配置Webhook URL")
                return

            # 创建通用的webhook消息格式
            webhook_payload = {
                "report_type": report.report_type,
                "generated_at": report.generated_at.isoformat(),
                "summary": report.summary or report.generate_summary(),
                "updates": [update.to_dict() for update in report.updates]
            }

            # 并发发送到所有webhook
            tasks = []
            for webhook_url in webhook_urls:
                tasks.append(self._send_single_webhook(webhook_url, webhook_payload))

            await asyncio.gather(*tasks, return_exceptions=True)
            self.logger.info(f"Webhook通知发送完成，共 {len(webhook_urls)} 个URL")

        except Exception as e:
            self.logger.error(f"发送Webhook通知失败: {e}")

    async def _send_single_webhook(self, webhook_url: str, payload: Dict[str, Any]):
        """发送单个webhook"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.settings.notification.webhook_timeout)
                ) as response:
                    if 200 <= response.status < 300:
                        self.logger.debug(f"Webhook发送成功: {webhook_url}")
                    else:
                        self.logger.error(f"Webhook发送失败 {webhook_url}: {response.status}")

        except Exception as e:
            self.logger.error(f"发送Webhook失败 {webhook_url}: {e}")

    async def test_notification(self, notification_type: NotificationType, config: Dict[str, Any]) -> bool:
        """测试通知配置"""
        try:
            # 创建测试报告
            from ..models.repository import RepositoryUpdate
            test_update = RepositoryUpdate(
                repo_name="test-repo",
                owner="test-owner",
                update_type="commits",
                title="测试通知",
                description="这是一个测试通知",
                url="https://github.com/test-owner/test-repo",
                author="test-user",
                created_at=report.generated_at
            )

            test_report = Report(
                report_type="test",
                updates=[test_update]
            )
            test_report.generate_summary()

            if notification_type == NotificationType.EMAIL:
                recipients = config.get('recipients', [])
                if recipients:
                    await self._send_email(recipients, "GitHub Sentinel 测试通知", test_report.to_text(), test_report.to_html())
                    return True

            elif notification_type == NotificationType.SLACK:
                webhook_url = config.get('webhook_url')
                if webhook_url:
                    message = self._format_slack_message(test_report)
                    async with aiohttp.ClientSession() as session:
                        async with session.post(webhook_url, json=message) as response:
                            return response.status == 200

            elif notification_type == NotificationType.DISCORD:
                webhook_url = config.get('webhook_url')
                if webhook_url:
                    message = self._format_discord_message(test_report)
                    async with aiohttp.ClientSession() as session:
                        async with session.post(webhook_url, json=message) as response:
                            return response.status == 204

            return False

        except Exception as e:
            self.logger.error(f"测试通知失败: {e}")
            return False
