"""
日志工具
"""
import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional


def setup_logger(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """设置日志配置"""
    logger = logging.getLogger("github_sentinel")

    # 避免重复设置
    if logger.handlers:
        return logger

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

    # 文件处理器
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """获取日志器"""
    if name:
        return logging.getLogger(f"github_sentinel.{name}")
    return logging.getLogger("github_sentinel")
