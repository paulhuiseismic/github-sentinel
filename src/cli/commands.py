"""
命令行界面
"""
import argparse
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.models.subscription import Subscription, NotificationType, UpdateFrequency, UpdateType
from src.services.subscription_service import SubscriptionService
from src.services.update_service import UpdateService
from src.services.notification_service import NotificationService
from src.config.settings import Settings
from src.utils.logger import setup_logger


class GitHubSentinelCLI:
    """GitHub Sentinel 命令行界面"""

    def __init__(self):
        self.settings = Settings.load_from_file()
        self.logger = setup_logger(self.settings.log_level, self.settings.log_file)
        self.subscription_service = SubscriptionService(self.settings)
        self.update_service = UpdateService(self.settings)
        self.notification_service = NotificationService(self.settings)

    def create_parser(self) -> argparse.ArgumentParser:
        """创建命令行参数解析器"""
        parser = argparse.ArgumentParser(
            prog='github-sentinel',
            description='GitHub Sentinel - 自动监控GitHub仓库更新'
        )

        subparsers = parser.add_subparsers(dest='command', help='可用命令')

        # 添加订阅命令
        add_parser = subparsers.add_parser('add', help='添加新的仓库订阅')
        add_parser.add_argument('repo_url', help='GitHub仓库URL')
        add_parser.add_argument('--frequency', choices=['daily', 'weekly', 'both'],
                               default='daily', help='更新频率')
        add_parser.add_argument('--notifications', nargs='+',
                               choices=['email', 'slack', 'discord', 'webhook'],
                               default=['email'], help='通知方式')
        add_parser.add_argument('--update-types', nargs='+',
                               choices=['commits', 'issues', 'pull_requests', 'releases', 'all'],
                               default=['all'], help='监控的更新类型')

        # 列出订阅命令
        list_parser = subparsers.add_parser('list', help='列出所有订阅')
        list_parser.add_argument('--active-only', action='store_true', help='只显示活跃订阅')

        # 删除订阅命令
        remove_parser = subparsers.add_parser('remove', help='删除订阅')
        remove_parser.add_argument('subscription_id', help='订阅ID')

        # 停用/激活订阅命令
        deactivate_parser = subparsers.add_parser('deactivate', help='停用订阅')
        deactivate_parser.add_argument('subscription_id', help='订阅ID')

        activate_parser = subparsers.add_parser('activate', help='激活订阅')
        activate_parser.add_argument('subscription_id', help='订阅ID')

        # 立即检查命令
        check_parser = subparsers.add_parser('check', help='立即检查更新')
        check_parser.add_argument('--days', type=int, default=1, help='检查最近几天的更新')

        # 状态命令
        status_parser = subparsers.add_parser('status', help='显示系统状态')

        # 测试命令
        test_parser = subparsers.add_parser('test', help='测试通知配置')
        test_parser.add_argument('notification_type', choices=['email', 'slack', 'discord', 'webhook'])

        return parser

    async def handle_add_subscription(self, args):
        """处理添加订阅命令"""
        try:
            # 解析仓库URL
            owner, repo_name = Subscription.parse_repo_url(args.repo_url)

            # 验证仓库是否存在
            if not await self.update_service.validate_subscription(
                Subscription.create_from_url(args.repo_url,
                                           notification_types=[NotificationType.EMAIL],
                                           frequency=UpdateFrequency.DAILY)
            ):
                print(f"❌ 仓库 {args.repo_url} 不存在或无法访问")
                return

            # 创建订阅
            subscription = Subscription.create_from_url(
                repo_url=args.repo_url,
                notification_types=[NotificationType(nt) for nt in args.notifications],
                frequency=UpdateFrequency(args.frequency),
                update_types=[UpdateType(ut) for ut in args.update_types]
            )

            if await self.subscription_service.add_subscription(subscription):
                print(f"✅ 成功添加订阅: {owner}/{repo_name}")
                print(f"   ID: {subscription.id}")
                print(f"   频率: {subscription.frequency.value}")
                print(f"   通知方式: {', '.join([nt.value for nt in subscription.notification_types])}")
            else:
                print(f"❌ 添加订阅失败")

        except Exception as e:
            print(f"❌ 添加订阅时出错: {e}")

    async def handle_list_subscriptions(self, args):
        """处理列出订阅命令"""
        try:
            if args.active_only:
                subscriptions = await self.subscription_service.get_active_subscriptions()
            else:
                subscriptions = await self.subscription_service.get_all_subscriptions()

            if not subscriptions:
                print("📭 没有订阅")
                return

            print(f"📋 共 {len(subscriptions)} 个订阅:")
            print()

            for sub in subscriptions:
                status = "🟢 活跃" if sub.is_active else "🔴 停用"
                last_checked = sub.last_checked.strftime("%Y-%m-%d %H:%M") if sub.last_checked else "从未检查"

                print(f"📌 {sub.owner}/{sub.repo_name}")
                print(f"   ID: {sub.id}")
                print(f"   状态: {status}")
                print(f"   频率: {sub.frequency.value}")
                print(f"   通知: {', '.join([nt.value for nt in sub.notification_types])}")
                print(f"   最后检查: {last_checked}")
                print()

        except Exception as e:
            print(f"❌ 列出订阅时出错: {e}")

    async def handle_remove_subscription(self, args):
        """处理删除订阅命令"""
        try:
            if await self.subscription_service.delete_subscription(args.subscription_id):
                print(f"✅ 成功删除订阅: {args.subscription_id}")
            else:
                print(f"❌ 删除订阅失败，ID不存在: {args.subscription_id}")

        except Exception as e:
            print(f"❌ 删除订阅时出错: {e}")

    async def handle_deactivate_subscription(self, args):
        """处理停用订阅命令"""
        try:
            if await self.subscription_service.deactivate_subscription(args.subscription_id):
                print(f"✅ 成功停用订阅: {args.subscription_id}")
            else:
                print(f"❌ 停用订阅失败，ID不存在: {args.subscription_id}")

        except Exception as e:
            print(f"❌ 停用订阅时出错: {e}")

    async def handle_activate_subscription(self, args):
        """处理激活订阅命令"""
        try:
            subscription = await self.subscription_service.get_subscription_by_id(args.subscription_id)
            if subscription:
                subscription.is_active = True
                if await self.subscription_service.update_subscription(subscription):
                    print(f"✅ 成功激活订阅: {args.subscription_id}")
                else:
                    print(f"❌ 激活订阅失败")
            else:
                print(f"❌ 订阅ID不存在: {args.subscription_id}")

        except Exception as e:
            print(f"❌ 激活订阅时出错: {e}")

    async def handle_check_updates(self, args):
        """处理检查更新命令"""
        try:
            print("🔍 正在检查更新...")
            subscriptions = await self.subscription_service.get_active_subscriptions()

            if not subscriptions:
                print("📭 没有活跃的订阅")
                return

            updates = await self.update_service.fetch_updates(subscriptions, days=args.days)

            if updates:
                print(f"📬 发现 {len(updates)} 个更新:")
                print()

                for update in updates[:10]:  # 只显示前10个
                    print(f"📝 {update.owner}/{update.repo_name}")
                    print(f"   类型: {update.update_type}")
                    print(f"   标题: {update.title}")
                    print(f"   作者: {update.author}")
                    print(f"   时间: {update.created_at.strftime('%Y-%m-%d %H:%M')}")
                    print()

                if len(updates) > 10:
                    print(f"... 还有 {len(updates) - 10} 个更新")
            else:
                print("📭 没有新的更新")

        except Exception as e:
            print(f"❌ 检查更新时出错: {e}")

    async def handle_status(self, args):
        """处理状态命令"""
        try:
            print("📊 GitHub Sentinel 状态:")
            print()

            # 订阅统计
            stats = await self.subscription_service.get_subscription_stats()
            print(f"📋 订阅统计:")
            print(f"   总订阅数: {stats['total_subscriptions']}")
            print(f"   活跃订阅: {stats['active_subscriptions']}")
            print(f"   停用订阅: {stats['inactive_subscriptions']}")
            print()

            # API状态
            api_status = await self.update_service.get_api_rate_limit_status()
            if api_status:
                print(f"🔌 GitHub API 状态:")
                print(f"   剩余请求: {api_status.get('remaining', 'N/A')}")
                print(f"   请求限制: {api_status.get('limit', 'N/A')}")
                print()

        except Exception as e:
            print(f"❌ 获取状态时出错: {e}")

    async def handle_test_notification(self, args):
        """处理测试通知命令"""
        try:
            print(f"🧪 测试 {args.notification_type} 通知...")

            # 这里需要根据通知类型获取相应的配置
            # 实际实现中应该提示用户输入相关配置
            config = {}

            if args.notification_type == 'email':
                print("请确保已在配置文件中设置邮件服务器信息")
                config = {'recipients': ['test@example.com']}
            elif args.notification_type in ['slack', 'discord']:
                print(f"请确保已在配置文件中设置 {args.notification_type} webhook URL")

            result = await self.notification_service.test_notification(
                NotificationType(args.notification_type), config
            )

            if result:
                print(f"✅ {args.notification_type} 通知测试成功")
            else:
                print(f"❌ {args.notification_type} 通知测试失败")

        except Exception as e:
            print(f"❌ 测试通知时出错: {e}")

    async def run(self, args):
        """运行CLI命令"""
        if args.command == 'add':
            await self.handle_add_subscription(args)
        elif args.command == 'list':
            await self.handle_list_subscriptions(args)
        elif args.command == 'remove':
            await self.handle_remove_subscription(args)
        elif args.command == 'deactivate':
            await self.handle_deactivate_subscription(args)
        elif args.command == 'activate':
            await self.handle_activate_subscription(args)
        elif args.command == 'check':
            await self.handle_check_updates(args)
        elif args.command == 'status':
            await self.handle_status(args)
        elif args.command == 'test':
            await self.handle_test_notification(args)
        else:
            print("❓ 未知命令，使用 --help 查看帮助")


def main():
    """CLI主函数"""
    cli = GitHubSentinelCLI()
    parser = cli.create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    asyncio.run(cli.run(args))


if __name__ == "__main__":
    main()
