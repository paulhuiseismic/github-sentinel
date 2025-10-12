"""
日志工具 - 支持按文件大小轮换和模块独立日志
"""
import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional


def setup_logger(log_level: str = "INFO", log_file: Optional[str] = None, logger_name: str = "github_sentinel") -> logging.Logger:
    """
    设置日志配置，支持按文件大小轮换

    Args:
        log_level: 日志级别
        log_file: 日志文件路径，如果为None则只输出到控制台
        logger_name: logger名称，用于区分不同模块

    Returns:
        配置好的logger实例
    """
    logger = logging.getLogger(logger_name)

    # 如果logger已经配置过且有正确的处理器，直接返回
    if logger.handlers and len(logger.handlers) > 0:
        # 检查是否已有文件处理器
        has_file_handler = any(isinstance(h, logging.handlers.RotatingFileHandler) for h in logger.handlers)
        has_console_handler = any(isinstance(h, logging.StreamHandler) and not isinstance(h, logging.handlers.RotatingFileHandler) for h in logger.handlers)

        # 如果需要文件日志但没有文件处理器，或者配置不完整，则重新配置
        if (log_file and not has_file_handler) or not has_console_handler:
            logger.handlers.clear()
        else:
            # 更新日志级别
            logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
            return logger

    # 清除现有处理器（如果需要重新配置）
    if not logger.handlers:
        logger.handlers.clear()

    # 防止日志向上传播到根logger，避免重复输出
    logger.propagate = False

    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # 创建统一的格式器
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器 - 按文件大小轮换
    if log_file:
        log_path = Path(log_file)
        log_dir = log_path.parent
        log_dir.mkdir(parents=True, exist_ok=True)

        # 使用RotatingFileHandler按文件大小轮换
        # maxBytes=1MB, backupCount=5 保留5个备份文件
        file_handler = logging.handlers.RotatingFileHandler(
            str(log_path),
            maxBytes=1024 * 1024,  # 1MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_web_logger(log_level: str = "INFO") -> logging.Logger:
    """获取Web服务专用logger"""
    return setup_logger(
        log_level=log_level,
        log_file="logs/web_service.log",
        logger_name="github_sentinel.web"
    )


def get_cli_logger(log_level: str = "INFO") -> logging.Logger:
    """获取CLI专用logger - 强制确保文件处理器正常工作"""
    logger_name = "github_sentinel.cli"

    # 每次都重新创建logger以确保配置正确
    # 先移除现有的logger
    if logger_name in logging.Logger.manager.loggerDict:
        del logging.Logger.manager.loggerDict[logger_name]

    logger = logging.getLogger(logger_name)
    logger.handlers.clear()
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

    # 文件处理器 - 强制创建
    log_path = Path("logs/cli.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # 直接写入一条测试消息验证文件可写
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write('')  # 确保文件可写

        file_handler = logging.handlers.RotatingFileHandler(
            str(log_path),
            maxBytes=1024 * 1024,  # 1MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # 立即测试文件写入
        logger.info("CLI Logger initialized successfully")
        file_handler.flush()

    except Exception as e:
        # 如果文件处理器创建失败，至少确保控制台输出正常
        logger.error(f"Failed to create file handler: {e}")

    return logger


def get_daemon_logger(log_level: str = "INFO") -> logging.Logger:
    """获取守护进程专用logger"""
    return setup_logger(
        log_level=log_level,
        log_file="logs/daemon.log",
        logger_name="github_sentinel.daemon"
    )


def get_main_logger(log_level: str = "INFO") -> logging.Logger:
    """获取主程序logger"""
    return setup_logger(
        log_level=log_level,
        log_file="logs/github_sentinel.log",
        logger_name="github_sentinel.main"
    )


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取日志器 - 保持向后兼容

    Args:
        name: logger名称，如果为None则返回默认logger

    Returns:
        logger实例
    """
    if name:
        return logging.getLogger(name)
    return logging.getLogger("github_sentinel")


def cleanup_old_logs(log_dir: str = "logs", max_files_per_logger: int = 10):
    """
    清理旧的日志文件，保持每个logger的文件数量在合理范围内

    Args:
        log_dir: 日志目录
        max_files_per_logger: 每个logger保留的最大文件数
    """
    try:
        log_path = Path(log_dir)
        if not log_path.exists():
            return

        # 按logger类型分组清理
        logger_prefixes = ['web_service', 'cli', 'daemon', 'github_sentinel']

        for prefix in logger_prefixes:
            # 找到所有相关的日志文件（包括轮换的备份文件）
            log_files = list(log_path.glob(f"{prefix}.log*"))

            # 按修改时间排序，保留最新的文件
            log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # 删除超出限制的旧文件
            for old_file in log_files[max_files_per_logger:]:
                try:
                    old_file.unlink()
                    print(f"已删除旧日志文件: {old_file}")
                except Exception as e:
                    print(f"删除日志文件 {old_file} 时出错: {e}")

    except Exception as e:
        print(f"清理日志文件时出错: {e}")
