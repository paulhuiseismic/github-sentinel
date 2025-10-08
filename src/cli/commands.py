"""
命令行界面
"""
import argparse
import asyncio
import sys
import json
from pathlib import Path
from typing import List, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.models.subscription import Subscription, NotificationType, UpdateFrequency, UpdateType
from src.services.subscription_service import SubscriptionService
from src.services.update_service import UpdateService
from src.services.notification_service import NotificationService
from src.services.github_service import GitHubService
from src.services.llm_service import LLMService, create_azure_openai_provider, create_openai_provider
from src.services.report_service import ReportService
from src.config.settings import Settings
from src.utils.logger import setup_logger


class GitHubSentinelCLI:
    """GitHub Sentinel 命令行界面"""

    def __init__(self):
        self.settings = Settings.from_env()  # 优先从环境变量加载
        try:
            # 尝试从配置文件加载（如果存在）
            file_settings = Settings.from_config_file()
            # 合并配置（环境变量优先）
            if not self.settings.github.token and file_settings.github.token:
                self.settings = file_settings
        except Exception:
            pass

        self.logger = setup_logger(self.settings.log_level, self.settings.log_file)

        # 初始化服务
        self.github_service = GitHubService(
            token=self.settings.github.token,
            rate_limit_per_hour=self.settings.github.rate_limit_per_hour,
            timeout=self.settings.github.timeout
        )

        self.llm_service = LLMService()
        self._setup_llm_providers()

        self.report_service = ReportService(self.llm_service, self.github_service)

        # 传统服务
        self.subscription_service = SubscriptionService(self.settings)
        self.update_service = UpdateService(self.settings)
        self.notification_service = NotificationService(self.settings)

    def _setup_llm_providers(self):
        """设置LLM提供商"""
        for provider_config in self.settings.llm_providers:
            try:
                if provider_config.type == "azure_openai":
                    provider = create_azure_openai_provider({
                        'model_name': provider_config.model_name,
                        'api_key': provider_config.api_key,
                        'azure_endpoint': provider_config.azure_endpoint,
                        'api_version': provider_config.api_version
                    })
                elif provider_config.type == "openai":
                    provider = create_openai_provider({
                        'model_name': provider_config.model_name,
                        'api_key': provider_config.api_key
                    })
                else:
                    self.logger.warning(f"不支持的LLM提供商类型: {provider_config.type}")
                    continue

                self.llm_service.add_provider(
                    provider_config.name,
                    provider,
                    provider_config.is_default
                )
                self.logger.info(f"已加载LLM提供商: {provider_config.name}")

            except Exception as e:
                self.logger.error(f"加载LLM提供商 {provider_config.name} 失败: {str(e)}")

    def create_parser(self) -> argparse.ArgumentParser:
        """创建命令行参数解析器"""
        parser = argparse.ArgumentParser(
            prog='github-sentinel',
            description='GitHub Sentinel - 自动监控GitHub仓库更新和智能报告生成'
        )

        subparsers = parser.add_subparsers(dest='command', help='可用命令')

        # === v0.1 传统命令 ===
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
        list_parser.add_argument('--format', choices=['table', 'json'],
                                default='table', help='输出格式')

        # 删除订阅命令
        remove_parser = subparsers.add_parser('remove', help='删除订阅')
        remove_parser.add_argument('repo_url', help='要删除的GitHub仓库URL')

        # 手动运行命令
        run_parser = subparsers.add_parser('run', help='手动运行检查')
        run_parser.add_argument('--repo', help='指定仓库（可选）')

        # === v0.2 新功能命令 ===
        # 生成每日进展报告
        progress_parser = subparsers.add_parser('progress', help='生成仓库每日进展报告')
        progress_parser.add_argument('owner', help='仓库所有者')
        progress_parser.add_argument('repo', help='仓库名称')
        progress_parser.add_argument('--output-dir', default='daily_progress',
                                   help='输出目录 (默认: daily_progress)')
        progress_parser.add_argument('--hours', type=int, default=24,
                                   help='时间范围（小时），默认24小时')
        progress_parser.add_argument('--compact', action='store_true', default=True,
                                   help='使用紧凑模式（默认开启，只显示merged PR和open issues）')
        progress_parser.add_argument('--full', action='store_true',
                                   help='使用完整模式（显示所有详细信息）')

        # 生成LLM摘要报告
        summary_parser = subparsers.add_parser('summary', help='使用LLM生成仓库摘要报告')
        summary_parser.add_argument('owner', help='仓库所有者')
        summary_parser.add_argument('repo', help='仓库名称')
        summary_parser.add_argument('--template', default='github_azure_prompt.txt',
                                  help='使用的提示模板')
        summary_parser.add_argument('--provider', help='LLM提供商名称')
        summary_parser.add_argument('--temperature', type=float, default=0.7,
                                  help='LLM温度参数')
        summary_parser.add_argument('--max-tokens', type=int, default=1500,
                                  help='最大生成令牌数（默认1500以节省成本）')
        summary_parser.add_argument('--hours', type=int, default=24,
                                   help='时间范围（小时），默认24小时')

        # 生成完整报告
        report_parser = subparsers.add_parser('report', help='生成完整的每日报告（进展+摘要）')
        report_parser.add_argument('owner', help='仓库所有者')
        report_parser.add_argument('repo', help='仓库名称')
        report_parser.add_argument('--template', default='github_azure_prompt.txt',
                                 help='使用的提示模板')
        report_parser.add_argument('--provider', help='LLM提供商名称')
        report_parser.add_argument('--temperature', type=float, default=0.7,
                                 help='LLM温度参数')
        report_parser.add_argument('--max-tokens', type=int, default=1500,
                                 help='最大生成令牌数（默认1500以节省成本）')
        report_parser.add_argument('--hours', type=int, default=24,
                                 help='时间范围（小时），默认24小时')
        report_parser.add_argument('--full', action='store_true',
                                 help='使用完整模式（显示所有详细信息）')

        # 批量生成报告
        batch_parser = subparsers.add_parser('batch', help='批量生成多个仓库的报告')
        batch_parser.add_argument('repos_file', help='包含仓库列表的JSON文件')
        batch_parser.add_argument('--template', default='github_azure_prompt.txt',
                                help='使用的提示模板')
        batch_parser.add_argument('--provider', help='LLM提供商名称')
        batch_parser.add_argument('--concurrent', type=int, default=3,
                                help='并发处理数量')

        # 对比不同模板/模型
        compare_parser = subparsers.add_parser('compare', help='对比不同模板和模型生成的报告')
        compare_parser.add_argument('owner', help='仓库所有者')
        compare_parser.add_argument('repo', help='仓库名称')
        compare_parser.add_argument('--templates', nargs='+',
                                  default=['github_azure_prompt.txt'],
                                  help='要对比的模板列表')
        compare_parser.add_argument('--providers', nargs='+',
                                  help='要对比的LLM提供商列表')

        # LLM提供商管理
        llm_parser = subparsers.add_parser('llm', help='LLM提供商管理')
        llm_subparsers = llm_parser.add_subparsers(dest='llm_action', help='LLM操作')

        llm_subparsers.add_parser('list', help='列出所有LLM提供商')

        test_parser = llm_subparsers.add_parser('test', help='测试LLM提供商')
        test_parser.add_argument('provider', help='提供商名称')
        test_parser.add_argument('--prompt', default='Hello, how are you?',
                               help='测试提示')

        # 报告历史管理
        history_parser = subparsers.add_parser('history', help='查看报告历史')
        history_parser.add_argument('repo', help='仓库名称')
        history_parser.add_argument('--limit', type=int, default=10,
                                  help='显示数量限制')

        return parser

    async def handle_command(self, args):
        """处理命令"""
        try:
            if args.command == 'add':
                await self._handle_add_subscription(args)
            elif args.command == 'list':
                await self._handle_list_subscriptions(args)
            elif args.command == 'remove':
                await self._handle_remove_subscription(args)
            elif args.command == 'run':
                await self._handle_run_check(args)
            # v0.2 新命令
            elif args.command == 'progress':
                await self._handle_progress_report(args)
            elif args.command == 'summary':
                await self._handle_summary_report(args)
            elif args.command == 'report':
                await self._handle_complete_report(args)
            elif args.command == 'batch':
                await self._handle_batch_reports(args)
            elif args.command == 'compare':
                await self._handle_compare_reports(args)
            elif args.command == 'llm':
                await self._handle_llm_commands(args)
            elif args.command == 'history':
                await self._handle_report_history(args)
            else:
                print("未知命令，使用 --help 查看帮助")
                return 1

        except Exception as e:
            self.logger.error(f"命令执行失败: {str(e)}")
            print(f"错误: {str(e)}")
            return 1

        return 0

    # === v0.2 新命令处理方法 ===
    async def _handle_progress_report(self, args):
        """处理进展报告命令"""
        from datetime import datetime, timedelta, timezone

        # 计算时间范围
        until = datetime.now(timezone.utc)
        since = until - timedelta(hours=args.hours)

        # 确定模式
        compact_mode = not args.full  # 默认紧凑模式，除非指定--full

        print(f"正在生成 {args.owner}/{args.repo} 的进展报告...")
        print(f"时间范围: 过去 {args.hours} 小时")
        print(f"模式: {'完整' if not compact_mode else '紧凑'}模式")

        progress_file = await self.report_service.generate_daily_progress_report(
            args.owner, args.repo, since=since, until=until, compact_mode=compact_mode
        )

        print(f"✅ 每日进展报告已生成: {progress_file}")

    async def _handle_summary_report(self, args):
        """处理摘要报告命令"""
        from datetime import datetime, timedelta, timezone

        # 计算时间范围
        until = datetime.now(timezone.utc)
        since = until - timedelta(hours=args.hours)

        print(f"正在使用LLM生成 {args.owner}/{args.repo} 的摘要报告...")
        print(f"时间范围: 过去 {args.hours} 小时")
        print(f"最大token数: {args.max_tokens}")

        # 先生成进展报告（使用紧凑模式节省token）
        progress_file = await self.report_service.generate_daily_progress_report(
            args.owner, args.repo, since=since, until=until, compact_mode=True
        )

        # 生成LLM摘要
        summary_file = await self.report_service.generate_llm_summary_report(
            args.repo,
            progress_file,
            args.template,
            args.provider,
            max_tokens=args.max_tokens,
            temperature=args.temperature
        )

        print(f"✅ 摘要报告已生成: {summary_file}")

    async def _handle_complete_report(self, args):
        """处理完整报告命令"""
        from datetime import datetime, timedelta, timezone

        # 计算时间范围
        until = datetime.now(timezone.utc)
        since = until - timedelta(hours=args.hours)

        # 确定模式
        compact_mode = not args.full

        print(f"正在生成 {args.owner}/{args.repo} 的完整报告...")
        print(f"时间范围: 过去 {args.hours} 小时")
        print(f"模式: {'完整' if not compact_mode else '紧凑'}模式")
        print(f"最大token数: {args.max_tokens}")

        result = await self.report_service.generate_complete_daily_report(
            args.owner,
            args.repo,
            template_name=args.template,
            provider_name=args.provider,
            since=since,
            until=until,
            compact_mode=compact_mode,
            max_tokens=args.max_tokens,
            temperature=args.temperature
        )

        print("✅ 完整报告已生成:")
        print(f"  - 进展报告: {result['progress_report']}")
        print(f"  - 摘要报告: {result['summary_report']}")
        print(f"  - 模式: {result['mode']}")
        print(f"  - 时间范围: {result['time_range']}")
        print(f"  - 生成时间: {result['generated_at']}")

    async def _handle_batch_reports(self, args):
        """处理批量报告命令"""
        # 读取仓库列表
        try:
            with open(args.repos_file, 'r', encoding='utf-8') as f:
                repos_data = json.load(f)
        except Exception as e:
            print(f"读取仓库列表文件失败: {str(e)}")
            return

        print(f"正在批量生成 {len(repos_data)} 个仓库的报告...")
        print("使用紧凑模式和较小token数量以节省成本...")

        results = await self.report_service.batch_generate_reports(
            repos_data,
            args.template,
            args.provider,
            compact_mode=True,  # 批量处理使用紧凑模式
            max_tokens=1200     # 批量处理使用更小的token数量
        )

        # 统计结果
        success_count = sum(1 for r in results if 'error' not in r)
        error_count = len(results) - success_count

        print(f"✅ 批量报告生成完成:")
        print(f"  - 成功: {success_count}")
        print(f"  - 失败: {error_count}")

        # 显示详细结果
        for result in results:
            if 'error' in result:
                print(f"  ❌ {result['repository']}: {result['error']}")
            else:
                print(f"  ✅ {result['repository']}: 报告已生成")

    async def _handle_compare_reports(self, args):
        """处理对比报告命令"""
        providers = args.providers or self.llm_service.list_providers()

        print(f"正在对比 {args.owner}/{args.repo} 的报告...")
        print(f"模板: {args.templates}")
        print(f"提供商: {providers}")

        result = await self.report_service.generate_report_with_multiple_templates(
            args.owner,
            args.repo,
            args.templates,
            providers[0] if providers else None  # 使用第一个提供商
        )

        print("✅ 对比报告已生成:")
        print(f"  - 原始报告: {result['progress_report']}")
        for template, summary_file in result['summaries'].items():
            if summary_file.startswith('ERROR:'):
                print(f"  ❌ {template}: {summary_file}")
            else:
                print(f"  ✅ {template}: {summary_file}")

    async def _handle_llm_commands(self, args):
        """处理LLM相关命令"""
        if args.llm_action == 'list':
            providers = self.llm_service.list_providers()
            if providers:
                print("可用的LLM提供商:")
                for provider_name in providers:
                    info = self.llm_service.get_provider_info(provider_name)
                    default_mark = " (默认)" if info['is_default'] else ""
                    print(f"  - {provider_name}: {info['model']} ({info['type']}){default_mark}")
            else:
                print("没有配置的LLM提供商")

        elif args.llm_action == 'test':
            print(f"正在测试LLM提供商: {args.provider}")
            try:
                response = await self.llm_service.generate_chat(
                    [{"role": "user", "content": args.prompt}],
                    args.provider
                )
                print(f"✅ 测试成功!")
                print(f"回复: {response}")
            except Exception as e:
                print(f"❌ 测试失败: {str(e)}")

    async def _handle_report_history(self, args):
        """处理报告历史命令"""
        history = self.report_service.get_report_history(args.repo, args.limit)

        if history:
            print(f"{args.repo} 的报告历史 (最近 {len(history)} 个):")
            for i, filepath in enumerate(history, 1):
                filename = Path(filepath).name
                print(f"  {i}. {filename}")
        else:
            print(f"没有找到 {args.repo} 的报告历史")

    # === v0.1 传统命令处理方法（保持向后兼容）===
    async def _handle_add_subscription(self, args):
        """处理添加订阅命令"""
        # 解析仓库URL
        repo_info = self._parse_repo_url(args.repo_url)
        if not repo_info:
            print(f"无效的仓库URL: {args.repo_url}")
            return

        # 创建订阅
        subscription = Subscription(
            repo_url=args.repo_url,
            owner=repo_info['owner'],
            repo_name=repo_info['repo'],
            frequency=UpdateFrequency(args.frequency),
            notification_types=[NotificationType(n) for n in args.notifications],
            update_types=[UpdateType(t) for t in args.update_types if t != 'all'] or list(UpdateType)
        )

        await self.subscription_service.add_subscription(subscription)
        print(f"✅ 已添加订阅: {args.repo_url}")

    async def _handle_list_subscriptions(self, args):
        """处理列出订阅命令"""
        subscriptions = await self.subscription_service.get_all_subscriptions()

        if not subscriptions:
            print("没有订阅的仓库")
            return

        if args.format == 'json':
            import json
            data = [s.to_dict() for s in subscriptions]
            print(json.dumps(data, indent=2, ensure_ascii=False, default=str))
        else:
            print(f"共有 {len(subscriptions)} 个订阅:")
            for i, sub in enumerate(subscriptions, 1):
                print(f"{i}. {sub.repo_url}")
                print(f"   频率: {sub.frequency.value}")
                print(f"   通知: {[n.value for n in sub.notification_types]}")
                print(f"   类型: {[t.value for t in sub.update_types]}")
                print()

    async def _handle_remove_subscription(self, args):
        """处理删除订阅命令"""
        await self.subscription_service.remove_subscription(args.repo_url)
        print(f"✅ 已删除订阅: {args.repo_url}")

    async def _handle_run_check(self, args):
        """处理手动运行检查命令"""
        if args.repo:
            repo_info = self._parse_repo_url(args.repo)
            if not repo_info:
                print(f"无效的仓库URL: {args.repo}")
                return
            # 运行单个仓库检查
            print(f"正在检查 {args.repo}...")
        else:
            # 运行所有订阅检查
            print("正在检查所有订阅的仓库...")

        await self.update_service.check_updates()
        print("✅ 检查完成")

    def _parse_repo_url(self, url: str) -> Optional[dict]:
        """解析GitHub仓库URL"""
        import re
        pattern = r'github\.com[/:]([\w\.-]+)/([\w\.-]+?)(?:\.git)?/?$'
        match = re.search(pattern, url)
        if match:
            return {'owner': match.group(1), 'repo': match.group(2)}
        return None


def main():
    """主函数"""
    try:
        cli = GitHubSentinelCLI()
        parser = cli.create_parser()
        args = parser.parse_args()

        if not args.command:
            parser.print_help()
            return 1

        # 运行异步命令
        return asyncio.run(cli.handle_command(args))
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        return 1
    except Exception as e:
        print(f"程序运行错误: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(main())
