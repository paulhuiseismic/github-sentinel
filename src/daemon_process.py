#!/usr/bin/env python3
"""
GitHub Sentinel 守护进程
DaemonProcess - 专门用于后台运行GitHub Sentinel服务（跨平台支持）
"""
import os
import sys
import time
import signal
import atexit
import subprocess
import threading
from pathlib import Path
from datetime import datetime
import platform

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.main import GitHubSentinel
from src.config.settings import Settings
from src.utils.logger import get_daemon_logger


class DaemonProcess:
    """GitHub Sentinel 守护进程类（跨平台支持）"""

    def __init__(self):
        """初始化守护进程"""
        self.name = "github_sentinel_daemon"
        self.pid_file = Path("run/github_sentinel.pid")
        self.log_file = "logs/daemon.log"
        self.working_dir = Path.cwd()
        self.is_windows = platform.system() == 'Windows'

        # 确保目录存在
        self.pid_file.parent.mkdir(parents=True, exist_ok=True)
        Path("logs").mkdir(parents=True, exist_ok=True)

        # 使用专用的守护进程logger
        self.logger = get_daemon_logger("INFO")

        # 进程状态
        self.is_running = False
        self.sentinel = None
        self.process = None

        # 标记是否为实际的守护进程（只有守护进程才需要注册清理函数）
        self.is_daemon_instance = False

    def write_pid_file(self):
        """写入PID文件"""
        try:
            current_pid = os.getpid()
            with open(self.pid_file, 'w') as f:
                f.write(str(current_pid))
            self.logger.info(f"PID file written: {self.pid_file} with PID: {current_pid}")
        except Exception as e:
            self.logger.error(f"Failed to write PID file: {e}")

    def create_daemon_subprocess(self):
        """创建守护进程子进程"""
        try:
            if self.is_windows:
                # Windows下使用subprocess创建后台进程
                import subprocess

                # 创建启动脚本参数
                args = [
                    sys.executable,
                    str(Path(__file__)),
                    "_run_daemon"  # 内部标志，表示运行守护进程主循环
                ]

                # Windows下创建无窗口的后台进程
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

                self.process = subprocess.Popen(
                    args,
                    cwd=str(self.working_dir),
                    startupinfo=startupinfo,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL
                )

                # 注意：不在这里写入PID文件，让子进程自己写入
                # 这样确保PID文件中的PID与实际运行的进程一致
                self.logger.info(f"Windows daemon subprocess started with PID: {self.process.pid}")

                # 等待一下确保子进程完全启动
                time.sleep(2)  # 增加等待时间

                # 检查进程是否还在运行
                if self.process.poll() is None:
                    # 检查子进程是否已经写入了PID文��
                    for i in range(10):  # 最多等待10秒
                        if self.pid_file.exists():
                            break
                        time.sleep(1)
                    return True
                else:
                    self.logger.error(f"Daemon subprocess exited immediately with code: {self.process.returncode}")
                    return False

            else:
                # Unix/Linux系统使用传统的fork方式
                return self._unix_daemonize()

        except Exception as e:
            self.logger.error(f"Failed to create daemon subprocess: {e}", exc_info=True)
            return False

    def _unix_daemonize(self):
        """Unix/Linux系统的守护进程化"""
        try:
            # 第一次fork
            pid = os.fork()
            if pid > 0:
                # 父进程退出
                sys.exit(0)
        except OSError as e:
            self.logger.error(f"第一次fork失败: {e}")
            return False

        # 脱离父进程会话
        os.chdir(str(self.working_dir))
        os.setsid()
        os.umask(0)

        try:
            # 第二次fork
            pid = os.fork()
            if pid > 0:
                # 父进程退出
                sys.exit(0)
        except OSError as e:
            self.logger.error(f"第二次fork失败: {e}")
            return False

        # 重定向标准输入输出
        sys.stdout.flush()
        sys.stderr.flush()

        # 写入PID文件
        self.write_pid_file()

        self.logger.info(f"Unix守护进程已启动，PID: {os.getpid()}")
        return True

    def read_pid_file(self):
        """读取PID文件"""
        try:
            if self.pid_file.exists():
                with open(self.pid_file, 'r') as f:
                    content = f.read().strip()
                    if content:  # 确保文件不为空
                        return int(content)
        except (ValueError, IOError) as e:
            self.logger.warning(f"读取PID文件失败: {e}")
        return None

    def remove_pid_file(self):
        """删除PID文件"""
        try:
            if self.pid_file.exists():
                self.pid_file.unlink()
                # 使用英文消息避免编码问题
                self.logger.info(f"PID file removed: {self.pid_file}")
        except Exception as e:
            self.logger.error(f"Failed to remove PID file: {e}")

    def is_process_running(self, pid):
        """检查进程是否在运行（跨平台）"""
        try:
            if self.is_windows:
                import psutil
                try:
                    process = psutil.Process(pid)
                    return process.is_running()
                except psutil.NoSuchProcess:
                    return False
            else:
                # Unix/Linux系统
                os.kill(pid, 0)
                return True
        except (OSError, ImportError):
            return False

    def setup_signal_handlers(self):
        """设置信号处理器"""
        def signal_handler(signum, frame):
            self.logger.info(f"收到信号 {signum}，正在关闭守护进程...")
            self.is_running = False
            if self.sentinel:
                self.sentinel.stop()
            self.cleanup()
            sys.exit(0)

        if self.is_windows:
            # Windows信号处理
            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)
            if hasattr(signal, 'SIGBREAK'):
                signal.signal(signal.SIGBREAK, signal_handler)
        else:
            # Unix/Linux信号处理
            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)

    def start(self, foreground=False):
        """启动守护进程"""
        # 检查是否已经在运行
        pid = self.read_pid_file()
        if pid and self.is_process_running(pid):
            print(f"守护进程已在运行，PID: {pid}")
            return False

        if not foreground:
            # 守护进程模式
            if self.is_windows:
                # Windows下创建子进程
                success = self.create_daemon_subprocess()
                if success:
                    print("守护进程启动成功")
                    return True
                else:
                    print("守护进程启动失败")
                    return False
            else:
                # Unix/Linux下使用fork
                if self._unix_daemonize():
                    # 这里是子进程，运行主循环
                    self.setup_signal_handlers()
                    self.run()
                    return True
                else:
                    return False
        else:
            # 前台模式
            self.write_pid_file()
            self.setup_signal_handlers()
            self.run()
            return True

    def stop(self):
        """停止守护进程"""
        pid = self.read_pid_file()
        if not pid:
            print("守护进程未运行")
            return True

        if not self.is_process_running(pid):
            print("守护进程已停止")
            self.remove_pid_file()
            return True

        try:
            if self.is_windows:
                # Windows下终止进程
                import psutil
                try:
                    process = psutil.Process(pid)
                    process.terminate()
                    # 等待进程结束
                    process.wait(timeout=10)
                except psutil.TimeoutExpired:
                    # 强制杀死进程
                    process.kill()
            else:
                # Unix/Linux系统
                os.kill(pid, signal.SIGTERM)

                # 等待进程停止
                for _ in range(30):  # 最多等待30秒
                    if not self.is_process_running(pid):
                        break
                    time.sleep(1)

                # 如果还在运行，强制终止
                if self.is_process_running(pid):
                    print("强制终止守护进程...")
                    os.kill(pid, signal.SIGKILL)

            self.remove_pid_file()
            print("守护进程已停止")
            return True

        except (ProcessLookupError, ImportError):
            print("守护进程已不存在")
            self.remove_pid_file()
            return True
        except Exception as e:
            print(f"停止守护进程失败: {e}")
            return False

    def status(self):
        """获取守护进程状态"""
        pid = self.read_pid_file()

        if not pid:
            return {
                "status": "stopped",
                "pid": None,
                "message": "PID文件不存在"
            }

        if self.is_process_running(pid):
            return {
                "status": "running",
                "pid": pid,
                "message": "守护进程正常运行"
            }
        else:
            return {
                "status": "dead",
                "pid": pid,
                "message": "PID文件存在但进程未运行"
            }

    def restart(self):
        """重启守护进程"""
        print("重启守护进程...")
        self.stop()
        time.sleep(2)  # 等待完全停止
        return self.start()

    def run(self):
        """运行主循环"""
        self.is_running = True
        self.is_daemon_instance = True  # 标记这是实际的守护进程实例

        # 只在守护进程中注册清理函数
        atexit.register(self.cleanup)

        self.logger.info("守护进程主循环开始运行")

        try:
            # 初始化GitHub Sentinel
            self.sentinel = GitHubSentinel()
            self.logger.info("GitHub Sentinel初始化完成")

            # 启动GitHub Sentinel
            self.sentinel.start()

        except Exception as e:
            self.logger.error(f"守护进程运行失败: {e}", exc_info=True)
            self.cleanup()
            sys.exit(1)

    def cleanup(self):
        """清理资源"""
        self.logger.info("清理守护进程资源...")
        self.is_running = False

        if self.sentinel:
            try:
                self.sentinel.stop()
            except:
                pass

        self.remove_pid_file()


def main():
    """主函数"""
    import argparse

    # 检查是否是内部守护进程调用
    if len(sys.argv) > 1 and sys.argv[1] == "_run_daemon":
        # 这是守护进程子进程，直接运行主循环
        daemon = DaemonProcess()
        daemon.write_pid_file()
        daemon.setup_signal_handlers()
        daemon.run()
        return

    parser = argparse.ArgumentParser(description="GitHub Sentinel 守护进程")
    parser.add_argument("action", choices=["start", "stop", "restart", "status"],
                       help="要执行的操作")
    parser.add_argument("--foreground", "-f", action="store_true",
                       help="前台运行模式")

    args = parser.parse_args()

    daemon = DaemonProcess()

    if args.action == "start":
        if daemon.start(foreground=args.foreground):
            if args.foreground:
                print("守护进程在前台运行中...")
            else:
                print("守护进程已启动")
        else:
            sys.exit(1)

    elif args.action == "stop":
        if not daemon.stop():
            sys.exit(1)

    elif args.action == "restart":
        if not daemon.restart():
            sys.exit(1)

    elif args.action == "status":
        status = daemon.status()
        print(f"守护进程状态: {status['status']}")
        if status['pid']:
            print(f"PID: {status['pid']}")
        print(f"消息: {status['message']}")


if __name__ == "__main__":
    main()
