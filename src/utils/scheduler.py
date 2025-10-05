"""
任务调度器
"""
import asyncio
import schedule
import threading
from typing import Callable, Optional
from datetime import datetime
import logging


class TaskScheduler:
    """任务调度器"""

    def __init__(self):
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.logger = logging.getLogger(__name__)

    def schedule_daily_task(self, task: Callable, time: str = "09:00"):
        """调度每日任务"""
        schedule.every().day.at(time).do(self._schedule_async_task, task)
        self.logger.info(f"已调度每日任务，执行时间: {time}")

    def schedule_weekly_task(self, task: Callable, day: str = "monday", time: str = "09:00"):
        """调度每周任务"""
        getattr(schedule.every(), day.lower()).at(time).do(self._schedule_async_task, task)
        self.logger.info(f"已调度每周任务，执行时间: {day} {time}")

    def _schedule_async_task(self, task: Callable):
        """调度异步任务"""
        if self.loop and not self.loop.is_closed():
            try:
                asyncio.run_coroutine_threadsafe(task(), self.loop)
            except Exception as e:
                self.logger.error(f"调度异步任务失败: {e}")
        else:
            self.logger.error("事件循环不可用，无法执行任务")

    def start(self):
        """启动调度器"""
        if self.is_running:
            self.logger.warning("调度器已在运行")
            return

        self.is_running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        self.logger.info("任务调度器已启动")

    def _run_scheduler(self):
        """运行调度循环"""
        # 创建新的事件循环
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        try:
            while self.is_running:
                schedule.run_pending()
                # 使用事件循环的sleep，避免阻塞
                self.loop.run_until_complete(asyncio.sleep(60))

        except Exception as e:
            self.logger.error(f"调度器运行错误: {e}")
        finally:
            if self.loop and not self.loop.is_closed():
                self.loop.close()

    def stop(self):
        """停止调度器"""
        if not self.is_running:
            return

        self.is_running = False

        # 停止事件循环
        if self.loop and not self.loop.is_closed():
            self.loop.call_soon_threadsafe(self.loop.stop)

        # 等待线程结束
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)

        self.logger.info("任务调度器已停止")
