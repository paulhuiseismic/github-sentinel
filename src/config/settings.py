"""
GitHub Sentinel 配置管理
"""
import os
import yaml
from dataclasses import dataclass
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class GitHubConfig:
    """GitHub API 配置"""
    token: str
    api_url: str = "https://api.github.com"
    rate_limit_per_hour: int = 5000
    timeout: int = 30


@dataclass
class NotificationConfig:
    """通知配置"""
    email_smtp_server: Optional[str] = None
    email_port: int = 587
    email_username: Optional[str] = None
    email_password: Optional[str] = None
    email_use_tls: bool = True
    slack_webhook_url: Optional[str] = None
    discord_webhook_url: Optional[str] = None
    webhook_timeout: int = 10


@dataclass
class DatabaseConfig:
    """数据库配置"""
    type: str = "json"  # json, sqlite, postgresql
    path: str = "data/subscriptions.json"
    connection_string: Optional[str] = None


@dataclass
class Settings:
    """应用设置"""
    github: GitHubConfig
    notification: NotificationConfig
    database: DatabaseConfig
    log_level: str = "INFO"
    log_file: str = "logs/github_sentinel.log"
    daily_scan_time: str = "09:00"
    weekly_scan_time: str = "09:00"
    weekly_scan_day: str = "monday"
    reports_dir: str = "data/reports"
    max_concurrent_requests: int = 5

    @classmethod
    def load_from_file(cls, config_path: Optional[str] = None) -> 'Settings':
        """从配置文件加载设置"""
        if config_path is None:
            # 查找配置文件
            possible_paths = [
                "src/config/config.yaml",
                "config/config.yaml",
                "config.yaml"
            ]

            config_path = None
            for path in possible_paths:
                if Path(path).exists():
                    config_path = path
                    break

        if config_path and Path(config_path).exists():
            return cls._load_from_yaml(config_path)
        else:
            # 使用环境变量创建默认配置
            return cls._load_from_env()

    @classmethod
    def _load_from_yaml(cls, config_path: str) -> 'Settings':
        """从YAML文件加载配置"""
        with open(config_path, 'r', encoding='utf-8') as file:
            config_data = yaml.safe_load(file) or {}

        # 从环境变量获取敏感信息
        github_token = os.getenv('GITHUB_TOKEN') or config_data.get('github', {}).get('token')
        if not github_token:
            raise ValueError("GitHub token is required. Set GITHUB_TOKEN environment variable or add it to config file.")

        github_data = config_data.get('github', {})
        github_data['token'] = github_token
        github_config = GitHubConfig(**github_data)

        notification_config = NotificationConfig(**config_data.get('notification', {}))
        database_config = DatabaseConfig(**config_data.get('database', {}))

        return cls(
            github=github_config,
            notification=notification_config,
            database=database_config,
            **{k: v for k, v in config_data.items()
               if k not in ['github', 'notification', 'database']}
        )

    @classmethod
    def _load_from_env(cls) -> 'Settings':
        """从环境变量加载配置"""
        github_token = os.getenv('GITHUB_TOKEN')
        if not github_token:
            raise ValueError("GitHub token is required. Set GITHUB_TOKEN environment variable.")

        github_config = GitHubConfig(token=github_token)
        notification_config = NotificationConfig(
            email_smtp_server=os.getenv('EMAIL_SMTP_SERVER'),
            email_username=os.getenv('EMAIL_USERNAME'),
            email_password=os.getenv('EMAIL_PASSWORD'),
            slack_webhook_url=os.getenv('SLACK_WEBHOOK_URL'),
            discord_webhook_url=os.getenv('DISCORD_WEBHOOK_URL')
        )
        database_config = DatabaseConfig()

        return cls(
            github=github_config,
            notification=notification_config,
            database=database_config,
            log_level=os.getenv('LOG_LEVEL', 'INFO')
        )
