#!/usr/bin/env python3
"""
GitHub Sentinel Web界面启动脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.main import GitHubSentinel
from src.config.settings import Settings
from src.utils.logger import get_web_logger, cleanup_old_logs

def main():
    """启动Web界面"""
    print("🚀 启动 GitHub Sentinel Web界面...")
    print("=" * 50)

    try:
        # 首先设置日志
        settings = Settings.from_config_file()
        logger = get_web_logger(settings.log_level)

        # 清理旧日志文件
        cleanup_old_logs("logs", 10)

        logger.info("=" * 50)
        logger.info("GitHub Sentinel Web界面启动中...")
        logger.info("入口类型: Web界面")

        sentinel = GitHubSentinel()
        logger.info("Web服务器配置: 0.0.0.0:7860")

        sentinel.start_web(
            server_name="0.0.0.0",
            server_port=7860,
            share=False
        )
    except ImportError as e:
        print("❌ 缺少必要的依赖包")
        print("请运行以下命令安装依赖:")
        print("pip install gradio>=4.0.0 pandas")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Web界面已关闭")
        if 'logger' in locals():
            logger.info("Web界面被用户关闭")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        if 'logger' in locals():
            logger.error(f"Web界面启动失败: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
