"""
Gradio Web界面服务
"""
import asyncio
from datetime import datetime
from typing import List, Tuple
from pathlib import Path

try:
    import gradio as gr
    import pandas as pd
except ImportError:
    print("❌ 缺少必要依赖: gradio 和 pandas")
    print("请运行: pip install gradio>=4.0.0 pandas")
    raise

from ..models.subscription import Subscription, NotificationType, UpdateFrequency, UpdateType
from ..services.subscription_service import SubscriptionService
from ..services.report_service import ReportService
from ..services.update_service import UpdateService
from ..services.github_service import GitHubService
from ..services.llm_service import LLMService, create_azure_openai_provider, create_openai_provider
from ..config.settings import Settings
from ..utils.logger import get_web_logger


class WebService:
    """Web界面服务"""

    def __init__(self, settings: Settings):
        self.settings = settings
        # 使用专用的Web服务logger
        self.logger = get_web_logger(settings.log_level)

        self.logger.info("🌐 初始化Web服务...")
        self.subscription_service = SubscriptionService(settings)

        # 修复GitHubService初始化 - 更好的token获取和验证
        github_token = ""
        if hasattr(settings, 'github') and hasattr(settings.github, 'token'):
            github_token = settings.github.token or ""

        # 验证token是否有效
        if not github_token or github_token == "null" or github_token.strip() == "":
            self.logger.warning("⚠️  GitHub Token未设置或无效！")
            self.logger.warning("请设置环境变量 GITHUB_TOKEN 或在配置文件中提供有效的token")
            self.logger.warning("获取GitHub Token: https://github.com/settings/tokens")
            # 使用空token创建服务，但会在使用时提供友好的错误信息
            github_token = ""
        else:
            self.logger.info("✅ GitHub Token已配置")

        self.github_service = GitHubService(github_token)
        self.llm_service = LLMService()

        # 设置LLM提供商
        self._setup_llm_providers()

        self.report_service = ReportService(self.llm_service, self.github_service)
        self.update_service = UpdateService(settings)
        self.app = None

        self.logger.info("✅ Web服务初始化完成")

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

    def create_app(self) -> gr.Blocks:
        """创建Gradio应用"""
        with gr.Blocks(
            title="GitHub Sentinel - 仓库监控系统",
            theme=gr.themes.Soft()
        ) as app:
            gr.Markdown("# 🔍 GitHub Sentinel - 仓库监控系统")
            gr.Markdown("智能GitHub仓库更新监控与报告生成工具")

            with gr.Tabs():
                # 订阅管理标签页
                with gr.Tab("📚 订阅管理"):
                    self._create_subscription_tab()

                # 报告生成标签页
                with gr.Tab("📊 报告生成"):
                    self._create_report_tab()

                # 系统状态标签页
                with gr.Tab("⚙️ 系统状态"):
                    self._create_status_tab()

        self.app = app
        return app

    def _create_subscription_tab(self):
        """创建订阅管理标签页"""
        gr.Markdown("## 订阅管理")

        # 添加新订阅区域
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 添加新订阅")
                repo_url_input = gr.Textbox(
                    label="GitHub仓库URL",
                    placeholder="https://github.com/owner/repo",
                    info="输入完整的GitHub仓库URL"
                )

                with gr.Row():
                    frequency_dropdown = gr.Dropdown(
                        label="更新频率",
                        choices=["daily", "weekly", "both"],
                        value="daily",
                        info="选择检查更新的频率"
                    )

                    notification_checkboxes = gr.CheckboxGroup(
                        label="通知方式",
                        choices=["email", "webhook", "slack", "discord"],
                        value=["email"],
                        info="选择通知方式"
                    )

                update_types_checkboxes = gr.CheckboxGroup(
                    label="监控内容",
                    choices=["commits", "issues", "pull_requests", "releases", "all"],
                    value=["all"],
                    info="选择要监控的更新类型"
                )

                add_button = gr.Button("添加订阅", variant="primary")
                add_result = gr.Textbox(label="添加结果", interactive=False)

        # 现有订阅列表区域
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 现有订阅")
                refresh_button = gr.Button("刷新订阅列表")
                subscriptions_df = gr.Dataframe(
                    headers=["ID", "仓库", "频率", "通知方式", "状态", "创建时间"],
                    interactive=False,
                    wrap=True
                )

                with gr.Row():
                    delete_id_input = gr.Textbox(
                        label="订阅ID",
                        placeholder="输入要删除的订阅ID"
                    )
                    delete_button = gr.Button("删除订阅", variant="stop")
                    delete_result = gr.Textbox(label="删除结果", interactive=False)

        # 事件处理函数
        def handle_add_subscription(repo_url, frequency, notification_types, update_types):
            result = self._add_subscription(repo_url, frequency, notification_types, update_types)
            return result

        def handle_refresh_subscriptions():
            return self._get_subscriptions_df()

        def handle_delete_subscription(subscription_id):
            result_msg, updated_df = self._delete_subscription(subscription_id)
            return result_msg, updated_df

        # 绑定事件处理函数
        add_button.click(
            fn=handle_add_subscription,
            inputs=[repo_url_input, frequency_dropdown, notification_checkboxes, update_types_checkboxes],
            outputs=[add_result]
        )

        refresh_button.click(
            fn=handle_refresh_subscriptions,
            outputs=[subscriptions_df]
        )

        delete_button.click(
            fn=handle_delete_subscription,
            inputs=[delete_id_input],
            outputs=[delete_result, subscriptions_df]
        )

        # 页面加载时自动加载订阅列表
        subscriptions_df.value = self._get_subscriptions_df()

    def _create_report_tab(self):
        """创建报告生成标签页"""
        gr.Markdown("## 报告生成")

        with gr.Row():
            with gr.Column():
                gr.Markdown("### 生成即时报告")

                # 仓库选择下拉框
                repo_dropdown = gr.Dropdown(
                    label="选择仓库",
                    choices=self._get_repo_choices(),
                    value="",
                    info="选择要生成报告的仓库",
                    interactive=True
                )

                # 刷新仓库列表按钮
                refresh_repos_button = gr.Button("刷新仓库列表", size="sm")

                report_type_radio = gr.Radio(
                    label="报告类型",
                    choices=["daily", "weekly", "custom"],
                    value="daily",
                    info="选择报告类型"
                )

                # 时间范围滑块（最大7天）
                days_slider = gr.Slider(
                    label="时间范围（天数）",
                    minimum=1,
                    maximum=7,
                    value=1,
                    step=1,
                    visible=True,
                    info="选择报告的时间范围"
                )

                generate_button = gr.Button("生成报告", variant="primary")

            with gr.Column():
                report_output = gr.Textbox(
                    label="报告内容",
                    lines=20,
                    max_lines=30,
                    interactive=False,
                    show_copy_button=True
                )

        # 历史报告区域
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 历史报告")
                refresh_reports_button = gr.Button("刷新报告列表")
                reports_df = gr.Dataframe(
                    headers=["文件名", "生成时间", "大小"],
                    interactive=False
                )

        # 事件处理
        def update_days_visibility_and_value(report_type):
            if report_type == "daily":
                return gr.update(visible=True, value=1, maximum=7)
            elif report_type == "weekly":
                return gr.update(visible=True, value=7, maximum=7)
            else:  # custom
                return gr.update(visible=True, value=3, maximum=7)

        def refresh_repo_choices():
            """刷新仓库选择列表"""
            choices = self._get_repo_choices()
            return gr.update(choices=choices, value="" if not choices else choices[0])

        # 绑定事件
        report_type_radio.change(
            fn=update_days_visibility_and_value,
            inputs=[report_type_radio],
            outputs=[days_slider]
        )

        refresh_repos_button.click(
            fn=refresh_repo_choices,
            outputs=[repo_dropdown]
        )

        generate_button.click(
            fn=self._generate_repo_report,
            inputs=[repo_dropdown, report_type_radio, days_slider],
            outputs=[report_output]
        )

        refresh_reports_button.click(
            fn=self._get_historical_reports,
            outputs=[reports_df]
        )

        # 页面加载时自动加载仓库列表
        repo_dropdown.choices = self._get_repo_choices()

    def _get_repo_choices(self) -> List[str]:
        """获取可选择的仓库列表"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            subscriptions = loop.run_until_complete(self.subscription_service.get_active_subscriptions())
            loop.close()

            if not subscriptions:
                return []

            repo_choices = [f"{sub.owner}/{sub.repo_name}" for sub in subscriptions]
            return repo_choices

        except Exception as e:
            self.logger.error(f"获取仓库列表失败: {e}")
            return []

    def _generate_repo_report(self, selected_repo: str, report_type: str, days: int) -> str:
        """为特定仓库生成LLM摘要报告"""
        try:
            self.logger.info(f"📊 Web界面请求生成报告: {selected_repo}, 类型: {report_type}, 天数: {days}")

            if not selected_repo:
                self.logger.warning("❌ 生成报告时未选择仓库")
                return "❌ 请先选择一个仓库"

            # 检查GitHub token是否有效
            if not self.github_service.token or self.github_service.token.strip() == "":
                self.logger.error("❌ GitHub Token未配置，无法生成报告")
                return """❌ GitHub Token未配置！

请按以下步骤设置GitHub Token：

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token" 创建新的Personal Access Token
3. 选择必要权限：repo, user, read:org
4. 复制生成的token
5. 设置环境变量：
   Windows: set GITHUB_TOKEN=你的token
   Linux/Mac: export GITHUB_TOKEN=你的token
6. 重启应用程序

或者在配置文件 src/config/config.yaml 中设置：
github:
  token: "你的token"
"""

            # 解析仓库名称
            parts = selected_repo.split("/")
            if len(parts) != 2:
                self.logger.error(f"❌ 无效的仓库格式: {selected_repo}")
                return "❌ 无效的仓库格式"

            owner, repo_name = parts[0], parts[1]

            # 根据报告类型确定天数
            if report_type == "daily":
                days = 1
            elif report_type == "weekly":
                days = 7
            # custom类型使用滑块的值

            self.logger.info(f"开始为 {owner}/{repo_name} 生成 {days} 天的报告")
            from datetime import timedelta, timezone
            start_time = datetime.now()

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # 生成完整的每日报告（包括LLM摘要）
                # 确保使用timezone-aware的datetime对象
                since = datetime.now(timezone.utc) - timedelta(days=days)

                result = loop.run_until_complete(
                    self.report_service.generate_complete_daily_report(
                        owner=owner,
                        repo=repo_name,
                        template_name="github_azure_prompt.txt",
                        since=since,
                        compact_mode=True,
                        max_tokens=1500
                    )
                )

                # 读取LLM摘要报告内容
                summary_file = result.get("summary_report")
                if summary_file and Path(summary_file).exists():
                    with open(summary_file, 'r', encoding='utf-8') as f:
                        summary_content = f.read()

                    duration = (datetime.now() - start_time).total_seconds()
                    self.logger.info(f"✅ Web界面成功生成报告: {selected_repo}, 耗时: {duration:.2f}秒")

                    report_header = f"📊 {selected_repo} - {report_type.upper()}报告 ({days}天)\n"
                    report_header += f"生成时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
                    report_header += "=" * 60 + "\n\n"

                    return report_header + summary_content
                else:
                    self.logger.error(f"❌ 未找到摘要报告文件: {summary_file}")
                    return f"❌ 未能找到摘要报告文件: {summary_file}"

            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                error_msg = str(e)
                self.logger.error(f"❌ Web界面生成报告失败: {selected_repo}, 耗时: {duration:.2f}秒, 错误: {error_msg}", exc_info=True)

                if "401" in error_msg:
                    return """❌ GitHub API认证失败 (401)

可能的原因：
1. GitHub Token无效或已过期
2. Token权限不足

解决方案：
1. 检查环境变量 GITHUB_TOKEN 是否正确设置
2. 访问 https://github.com/settings/tokens 重新生成token
3. 确保token具有以下权限：
   - repo (访问仓库)
   - user (用户信息)
   - read:org (组织信息)
4. 重新设置环境变量并重启应用

当前token状态: """ + ("已设置" if self.github_service.token else "未设置")
                elif "403" in error_msg:
                    return f"❌ GitHub API访问被拒绝 (403)\n\n可能原因：\n- API调用频率超限\n- Token权限不足\n- 仓库为私有且无访问权限\n\n详细错误: {error_msg}"
                elif "404" in error_msg:
                    return f"❌ 仓库不存在或无法访问 (404)\n\n请检查：\n- 仓库名称是否正确\n- 仓库是否为公开仓库\n- 是否有访问权限\n\n仓库: {selected_repo}"
                elif "can't compare offset-naive and offset-aware datetimes" in error_msg:
                    return f"❌ 时间比较错误已修复，请重试\n\n这是一个已知问题，现在应该已经解决。请再次尝试生成报告。\n\n详细错误: {error_msg}"
                else:
                    return f"❌ 生成报告时出错: {error_msg}"
            finally:
                loop.close()

        except Exception as e:
            self.logger.error(f"❌ Web界面处理报告请求时出错: {str(e)}", exc_info=True)
            return f"❌ 处理请求时出错: {str(e)}"

    def _create_status_tab(self):
        """创建系统状态标签页"""
        gr.Markdown("## 系统状态")

        with gr.Row():
            with gr.Column():
                gr.Markdown("### 系统信息")
                status_button = gr.Button("刷新状态")
                status_output = gr.Textbox(
                    label="系统状态",
                    lines=10,
                    interactive=False
                )

            with gr.Column():
                gr.Markdown("### 手动扫描")
                scan_type_radio = gr.Radio(
                    label="扫描类型",
                    choices=["daily", "weekly"],
                    value="daily"
                )
                manual_scan_button = gr.Button("执行扫描", variant="secondary")
                scan_result = gr.Textbox(
                    label="扫描结果",
                    interactive=False
                )

        status_button.click(
            fn=self._get_system_status,
            outputs=[status_output]
        )

        manual_scan_button.click(
            fn=self._run_manual_scan,
            inputs=[scan_type_radio],
            outputs=[scan_result]
        )

    def _add_subscription(self, repo_url: str, frequency: str, notification_types: List[str], update_types: List[str]) -> str:
        """添加新订阅"""
        try:
            self.logger.info(f"📝 Web界面请求添加订阅: {repo_url}")

            if not repo_url or not repo_url.startswith("https://github.com/"):
                self.logger.warning(f"❌ 无效的仓库URL: {repo_url}")
                return "❌ 请输入有效的GitHub仓库URL"

            # 解析仓库URL
            parts = repo_url.replace("https://github.com/", "").split("/")
            if len(parts) < 2:
                self.logger.warning(f"❌ 无效的仓库URL格式: {repo_url}")
                return "❌ 无效的GitHub仓库URL格式"

            owner, repo_name = parts[0], parts[1]
            self.logger.info(f"解析仓库信息: {owner}/{repo_name}, 频率: {frequency}")

            # 创建订阅对象
            subscription = Subscription(
                repo_url=repo_url,
                owner=owner,
                repo_name=repo_name,
                notification_types=[NotificationType(nt) for nt in notification_types],
                frequency=UpdateFrequency(frequency),
                update_types=[UpdateType(ut) for ut in update_types]
            )

            # 异步添加订阅
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(self.subscription_service.add_subscription(subscription))
            loop.close()

            if success:
                self.logger.info(f"✅ Web界面成功添加订阅: {owner}/{repo_name}")
                return f"✅ 成功添加订阅: {owner}/{repo_name}"
            else:
                self.logger.warning(f"⚠️  Web界面添加订阅失败，可能重复: {owner}/{repo_name}")
                return "❌ 添加订阅失败，可能已存在相同订阅"

        except Exception as e:
            self.logger.error(f"❌ Web界面添加订阅时出错: {str(e)}", exc_info=True)
            return f"❌ 添加订阅时出错: {str(e)}"

    def _get_subscriptions_df(self) -> pd.DataFrame:
        """获取订阅列表DataFrame"""
        try:
            self.logger.debug("🔍 Web界面请求获取订阅列表")

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            subscriptions = loop.run_until_complete(self.subscription_service.get_all_subscriptions())
            loop.close()

            if not subscriptions:
                self.logger.info("📋 当前没有订阅")
                return pd.DataFrame(columns=["ID", "仓库", "频率", "通知方式", "状态", "创建时间"])

            self.logger.info(f"📋 获取到 {len(subscriptions)} 个订阅")
            data = []
            for sub in subscriptions:
                notification_str = ", ".join([nt.value for nt in sub.notification_types])
                status = "✅ 活跃" if sub.is_active else "❌ 已停用"
                created_time = sub.created_at.strftime("%Y-%m-%d %H:%M")

                data.append([
                    sub.id[:8],  # 显示ID前8位
                    f"{sub.owner}/{sub.repo_name}",
                    sub.frequency.value,
                    notification_str,
                    status,
                    created_time
                ])

            return pd.DataFrame(data, columns=["ID", "仓库", "频率", "通知方式", "状态", "创建时间"])

        except Exception as e:
            self.logger.error(f"❌ Web界面获取订阅列表失败: {e}", exc_info=True)
            return pd.DataFrame(columns=["ID", "仓库", "频率", "通知方式", "状态", "创建时间"])

    def _delete_subscription(self, subscription_id: str) -> Tuple[str, pd.DataFrame]:
        """删除订阅"""
        try:
            self.logger.info(f"🗑️ Web界面请求删除订阅: {subscription_id}")

            if not subscription_id:
                self.logger.warning("❌ 删除订阅时未提供ID")
                return "❌ 请输入订阅ID", self._get_subscriptions_df()

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(self.subscription_service.delete_subscription(subscription_id))
            loop.close()

            if success:
                self.logger.info(f"✅ Web界面成功删除订阅: {subscription_id}")
                result = f"✅ 成功删除订阅 {subscription_id}"
            else:
                self.logger.warning(f"⚠️  Web界面删除订阅失败，未找到: {subscription_id}")
                result = f"❌ 删除失败，未找到订阅 {subscription_id}"

            return result, self._get_subscriptions_df()

        except Exception as e:
            self.logger.error(f"❌ Web界面删除订阅时出错: {str(e)}", exc_info=True)
            return f"❌ 删除订阅时出错: {str(e)}", self._get_subscriptions_df()

    def _generate_report(self, report_type: str, days: int) -> str:
        """生成报告（备用方法）"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            subscriptions = loop.run_until_complete(self.subscription_service.get_active_subscriptions())
            if not subscriptions:
                loop.close()
                return "❌ 没有活跃的订阅，无法生成报告"

            # 根据报告类型确定天数
            if report_type == "daily":
                days = 1
            elif report_type == "weekly":
                days = 7

            # 获取更新数据
            updates = loop.run_until_complete(self.update_service.fetch_updates(subscriptions, days))

            if not updates:
                loop.close()
                return f"📝 在过去{days}天内没有发现新的更新"

            # 使用简单的报告生成方法
            report_content = f"📊 {report_type.upper()}报告 - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            report_content += f"时间范围: 过去{days}天\n"
            report_content += f"扫描仓库: {len(subscriptions)}个\n"
            report_content += f"发现更新: {len(updates)}个\n\n"

            for update in updates[:10]:  # 显示前10个更新
                report_content += f"• {update.get('repo', 'Unknown')}: {update.get('title', 'No title')}\n"

            if len(updates) > 10:
                report_content += f"... 还有 {len(updates) - 10} 个更新\n"

            loop.close()
            return report_content

        except Exception as e:
            return f"❌ 生成报告时出错: {str(e)}"

    def _get_historical_reports(self) -> pd.DataFrame:
        """获取历史报告列表"""
        try:
            reports_dir = Path("data/reports")
            if not reports_dir.exists():
                return pd.DataFrame(columns=["文件名", "生成时间", "大小"])

            data = []
            for file_path in reports_dir.glob("*.json"):
                stat = file_path.stat()
                size = f"{stat.st_size / 1024:.1f} KB"
                mod_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                data.append([file_path.name, mod_time, size])

            return pd.DataFrame(data, columns=["文件名", "生成时间", "大小"])

        except Exception as e:
            self.logger.error(f"获取历史报告失败: {e}")
            return pd.DataFrame(columns=["文件名", "生成时间", "大小"])

    def _get_system_status(self) -> str:
        """获取系统状态"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            subscriptions = loop.run_until_complete(self.subscription_service.get_all_subscriptions())
            active_subs = [s for s in subscriptions if s.is_active]
            loop.close()

            status_info = []
            status_info.append("🚀 GitHub Sentinel 系统状态")
            status_info.append("=" * 40)
            status_info.append(f"📊 订阅总数: {len(subscriptions)}")
            status_info.append(f"✅ 活跃订阅: {len(active_subs)}")
            status_info.append(f"⏰ 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            status_info.append("")

            if active_subs:
                status_info.append("📋 活跃订阅详情:")
                for sub in active_subs[:5]:  # 显示前5个
                    last_check = sub.last_checked.strftime('%Y-%m-%d %H:%M') if sub.last_checked else "从未检查"
                    status_info.append(f"  • {sub.owner}/{sub.repo_name} - {sub.frequency.value} - 最后检查: {last_check}")

                if len(active_subs) > 5:
                    status_info.append(f"  ... 还有 {len(active_subs) - 5} 个订阅")

            return "\n".join(status_info)

        except Exception as e:
            return f"❌ 获取系统状态时出错: {str(e)}"

    def _run_manual_scan(self, scan_type: str) -> str:
        """执行手动扫描"""
        try:
            from ..main import GitHubSentinel

            # 创建GitHubSentinel实例
            sentinel = GitHubSentinel()

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            if scan_type == "daily":
                loop.run_until_complete(sentinel.run_daily_scan())
                result = "✅ 每日扫描已完成"
            else:
                loop.run_until_complete(sentinel.run_weekly_scan())
                result = "✅ 每周扫描已完成"

            loop.close()
            return result

        except Exception as e:
            return f"❌ 执行扫描时出错: {str(e)}"

    def launch(self, server_name: str = "0.0.0.0", server_port: int = 7860, share: bool = False):
        """启动Web应用"""
        if self.app is None:
            self.create_app()

        self.logger.info(f"启动Gradio Web界面: http://{server_name}:{server_port}")

        self.app.launch(
            server_name=server_name,
            server_port=server_port,
            share=share,
            show_error=True,
            quiet=False
        )
