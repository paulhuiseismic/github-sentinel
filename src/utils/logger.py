"""
日志工具
"""
import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


def setup_logger(log_level: str = "INFO", log_file: Optional[str] = None, logger_name: str = "github_sentinel") -> logging.Logger:
    """设置日志配置，支持按日期分文件存储"""
    logger = logging.getLogger(logger_name)

    # 如果logger已经配置过，直接返回，避免重复配置
    if logger.handlers and len(logger.handlers) > 0:
        return logger

    # 清除现有处理器，避免重复添加
    logger.handlers.clear()

    # 防止日志向上传播到根logger，避免重复输出
    logger.propagate = False

    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # 创建格式器
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器 - 按日期分文件
    if log_file:
        log_path = Path(log_file)
        log_dir = log_path.parent
        log_dir.mkdir(parents=True, exist_ok=True)

        # 生成带日期的日志文件名
        today = datetime.now().strftime('%Y-%m-%d')
        log_filename = f"{log_path.stem}_{today}.log"
        daily_log_file = log_dir / log_filename

        # 使用TimedRotatingFileHandler按天轮转
        file_handler = logging.handlers.TimedRotatingFileHandler(
            str(daily_log_file),
            when='midnight',
            interval=1,
            backupCount=30,  # 保留30天的日志
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.suffix = "%Y-%m-%d.log"
        logger.addHandler(file_handler)

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """获取日志器"""
    if name:
        return logging.getLogger(name)
    return logging.getLogger("github_sentinel")


def cleanup_old_logs(log_dir: str = "logs", days_to_keep: int = 30):
    """清理旧的日志文件"""
    try:
        log_path = Path(log_dir)
        if not log_path.exists():
            return

        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        for log_file in log_path.glob("*.log"):
            if log_file.stat().st_mtime < cutoff_date.timestamp():
                log_file.unlink()
                print(f"已删除旧日志文件: {log_file}")

    except Exception as e:
        print(f"清理日志文件时出错: {e}")
