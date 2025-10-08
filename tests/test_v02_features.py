#!/usr/bin/env python3
"""
GitHub Sentinel v0.2 测试脚本 - 优化版本（避免token限制）
"""
import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.github_service import GitHubService
from src.services.llm_service import LLMService, create_azure_openai_provider
from src.services.report_service import ReportService

async def test_v02_features():
    """测试v0.2功能"""
    print("🚀 GitHub Sentinel v0.2 功能测试 (优化版本)")

    # 检查环境变量
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("❌ 请设置 GITHUB_TOKEN 环境变量")
        return

    # 初始化GitHub服务
    github_service = GitHubService(token=github_token)
    print("✅ GitHub服务初始化成功")

    # 初始化LLM服务
    llm_service = LLMService()

    # 如果配置了Azure OpenAI，添加提供商
    azure_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

    if azure_key and azure_endpoint:
        try:
            provider = create_azure_openai_provider({
                'model_name': os.getenv("AZURE_OPENAI_MODEL", "gpt-4"),
                'api_key': azure_key,
                'azure_endpoint': azure_endpoint,
                'api_version': os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
            })
            llm_service.add_provider("azure_openai", provider, is_default=True)
            print("✅ Azure OpenAI提供商配置成功")
        except Exception as e:
            print(f"⚠️  Azure OpenAI配置失败: {e}")

    # 初始化报告服务
    report_service = ReportService(llm_service, github_service)
    print("✅ 报告服务初始化成功")

    # 测试功能
    try:
        print("\n📊 测试功能1: 生成紧凑模式进展报告（节省token）")

        # 使用较短的时间范围（12小时）和紧凑模式
        until = datetime.now(timezone.utc)
        since = until - timedelta(hours=12)  # 缩短到12小时

        progress_file = await report_service.generate_daily_progress_report(
            "microsoft", "vscode",
            since=since,
            until=until,
            compact_mode=True  # 使用紧凑模式
        )
        print(f"✅ 进展报告已生成: {progress_file}")

        # 检查文件大小
        with open(progress_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"📏 报告内容长度: {len(content)} 字符")

        if llm_service.list_providers():
            print("\n🤖 测试功能2: 生成LLM摘要报告（使用较小token数量）")

            # 使用更保守的参数设置
            summary_file = await report_service.generate_llm_summary_report(
                "vscode",
                progress_file,
                max_tokens=1000,  # 降低到1000 tokens
                temperature=0.5   # 降低温度以获得更确定的输出
            )
            print(f"✅ 摘要报告已生成: {summary_file}")

            # 读取并显示摘要内容片段
            with open(summary_file, 'r', encoding='utf-8') as f:
                summary_content = f.read()
                print(f"📄 摘要报告预览（前200字符）:")
                print(f"   {summary_content[:200]}...")

        else:
            print("⚠️  跳过LLM测试（未配置LLM提供商）")

        print("\n🎯 优化建议:")
        print("1. 使用紧凑模式减少内容长度")
        print("2. 缩短时间范围到12-24小时")
        print("3. 设置较小的max_tokens值 (1000-1500)")
        print("4. 降低temperature值以获得更稳定的输出")
        print("5. 只关注重要信息（已合并PR和活跃Issues）")

    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg and "rate limit" in error_msg.lower():
            print("❌ 遇到Azure OpenAI速率限制问题")
            print("💡 解决方案:")
            print("   1. 等待几分钟后重试")
            print("   2. 使用更小的时间范围 (--hours 6)")
            print("   3. 使用更小的max_tokens值 (--max-tokens 800)")
            print("   4. 升级到更高级别的Azure OpenAI定价层")
        else:
            print(f"❌ 测试失败: {e}")

async def test_minimal_example():
    """测试最小化示例（极少token使用）"""
    print("\n🧪 测试最小化示例（适用于S0定价层）")

    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("❌ 请设置 GITHUB_TOKEN 环境变量")
        return

    try:
        github_service = GitHubService(token=github_token)

        # 只获取过去6小时的已合并PR
        until = datetime.now(timezone.utc)
        since = until - timedelta(hours=6)

        # 直接调用GitHub API获取最少的数据
        pull_requests = await github_service.get_pull_requests(
            "microsoft", "vscode",
            since=since,
            until=until,
            per_page=5,  # 只获取5个PR
            merged_only=True,  # 只要已合并的
            include_body=False  # 不包含详细描述
        )

        print(f"✅ 获取到 {len(pull_requests)} 个已合并的PR")
        for pr in pull_requests[:3]:  # 只显示前3个
            print(f"   - #{pr['number']}: {pr['title'][:50]}...")

        # 如果有PR，创建一个极简报告
        if pull_requests:
            simple_report = f"""# vscode 简要进展

过去6小时已合并的PR ({len(pull_requests)}个):
{chr(10).join([f"- #{pr['number']}: {pr['title']}" for pr in pull_requests[:3]])}
"""
            print(f"📝 生成的简要报告:")
            print(simple_report)

    except Exception as e:
        print(f"❌ 最小化测试失败: {e}")

def test_cli_integration():
    """测试CLI集成"""
    print("\n🔧 测试CLI集成")

    # 测试CLI命令帮助
    try:
        import subprocess

        # 设置环境变量以避免编码问题
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'

        result = subprocess.run([
            sys.executable, "-m", "src.cli.commands", "--help"
        ], capture_output=True, text=True, cwd=project_root,
           encoding='utf-8', errors='replace', env=env)

        if result.returncode == 0:
            print("✅ CLI命令帮助正常")
            print("   可用命令包括: progress, summary, report, batch, llm, history")
        else:
            print(f"❌ CLI命令测试失败:")
            if result.stderr:
                # 安全地处理错误输出，避免编码问题
                error_msg = result.stderr.encode('utf-8', errors='replace').decode('utf-8')
                print(f"   错误信息: {error_msg[:200]}...")
            if result.stdout:
                stdout_msg = result.stdout.encode('utf-8', errors='replace').decode('utf-8')
                print(f"   输出信息: {stdout_msg[:200]}...")

        # 测试LLM提供商列表
        print("🔍 测试LLM提供商列表...")
        result = subprocess.run([
            sys.executable, "-m", "src.cli.commands", "llm", "list"
        ], capture_output=True, text=True, cwd=project_root,
           encoding='utf-8', errors='replace', env=env)

        if result.returncode == 0:
            print("✅ LLM提供商列表正常")
            # 安全地显示输出的一部分
            if result.stdout:
                output_lines = result.stdout.split('\n')
                for line in output_lines[:5]:  # 只显示前5行
                    if line.strip():
                        print(f"   {line}")
        else:
            print(f"❌ LLM提供商列表失败:")
            if result.stderr:
                error_msg = result.stderr.encode('utf-8', errors='replace').decode('utf-8')
                print(f"   错误信息: {error_msg[:200]}...")

    except Exception as e:
        print(f"❌ CLI集成测试失败: {e}")
        # 提供替代的简单测试
        print("🔄 尝试简化的CLI测试...")
        try:
            # 直接导入和测试CLI模块
            from src.cli.commands import GitHubSentinelCLI
            cli = GitHubSentinelCLI()
            parser = cli.create_parser()
            print("✅ CLI模块导入和初始化成功")

            # 测试解析器
            help_text = parser.format_help()
            if "progress" in help_text and "summary" in help_text:
                print("✅ CLI命令解析器正常，包含v0.2新命令")
            else:
                print("⚠️ CLI命令解析器可能缺少某些命令")

        except Exception as inner_e:
            print(f"❌ 简化CLI测试也失败: {inner_e}")

if __name__ == "__main__":
    print("GitHub Sentinel v0.2 测试套件")
    print("=" * 50)
    print("选择测试模式:")
    print("1. 标准测试（需要足够的token配额）")
    print("2. 最小化测试（适用于S0定价层）")
    print("3. CLI集成测试")
    print("4. 运行所有测试")

    choice = input("请输入选择 (1-4): ").strip()

    if choice == "2":
        asyncio.run(test_minimal_example())
    elif choice == "3":
        test_cli_integration()
    elif choice == "4":
        print("\n🚀 运行所有测试...")
        test_cli_integration()
        asyncio.run(test_minimal_example())
        asyncio.run(test_v02_features())
    else:
        asyncio.run(test_v02_features())
