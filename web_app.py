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

def main():
    """启动Web界面"""
    print("🚀 启动 GitHub Sentinel Web界面...")
    print("=" * 50)

    try:
        sentinel = GitHubSentinel()
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
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
