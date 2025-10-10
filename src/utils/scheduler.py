"""
任务调度器
"""
import asyncio
import schedule
import threading
from typing import Callable, Optional
from datetime import datetime
from ..utils.logger import get_logger


class TaskScheduler:
    """任务调度器"""

    def __init__(self):
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.logger = get_logger("github_sentinel.scheduler")

    def schedule_daily_task(self, task: Callable, time: str = "09:00"):
        """调度每日任务"""
        schedule.every().day.at(time).do(self._schedule_async_task, task, "每日任务")
        self.logger.info(f"✅ 已调度每日任务，执行时间: {time}")

    def schedule_weekly_task(self, task: Callable, day: str = "monday", time: str = "09:00"):
        """调度每周任务"""
        getattr(schedule.every(), day.lower()).at(time).do(self._schedule_async_task, task, "每周任务")
        self.logger.info(f"✅ 已调度每周任务，执行时间: {day} {time}")

    def _schedule_async_task(self, task: Callable, task_name: str = "未知任务"):
        """调度异步任务"""
        self.logger.info(f"🔄 开始执行调度任务: {task_name}")
        start_time = datetime.now()

        if self.loop and not self.loop.is_closed():
            try:
                future = asyncio.run_coroutine_threadsafe(task(), self.loop)
                # 等待任务完成
                future.result(timeout=300)  # 5分钟超时

                duration = (datetime.now() - start_time).total_seconds()
                self.logger.info(f"✅ {task_name}执行完成，耗时: {duration:.2f}秒")

            except asyncio.TimeoutError:
                self.logger.error(f"❌ {task_name}执行超时（5分钟）")
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                self.logger.error(f"❌ {task_name}执行失败，耗时: {duration:.2f}秒，错误: {e}", exc_info=True)
        else:
            self.logger.error(f"❌ 事件循环不可用，无法执行{task_name}")

    def start(self):
        """启动调度器"""
        if self.is_running:
            self.logger.warning("⚠️  调度器已在运行")
            return

        self.is_running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        self.logger.info("🚀 任务调度器已启动")

    def _run_scheduler(self):
        """运行调度器"""
        # 创建新的事件循环用于异步任务
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self.logger.info("📅 调度器线程开始运行")

        try:
            while self.is_running:
                schedule.run_pending()
                # 每分钟检查一次待执行的任务
                threading.Event().wait(60)

        except Exception as e:
            self.logger.error(f"❌ 调度器运行出错: {e}", exc_info=True)
        finally:
            if self.loop and not self.loop.is_closed():
                self.loop.close()
            self.logger.info("📅 调度器线程已停止")

    def stop(self):
        """停止调度器"""
        if not self.is_running:
            self.logger.warning("⚠️  调度器未在运行")
            return

        self.logger.info("🛑 正在停止任务调度器...")
        self.is_running = False

        # 清除所有调度任务
        schedule.clear()

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
            if self.thread.is_alive():
                self.logger.warning("⚠️  调度器线程停止超时")
            else:
                self.logger.info("✅ 调度器线程已正常停止")

        if self.loop and not self.loop.is_closed():
            self.loop.close()

        self.logger.info("🛑 任务调度器已停止")
