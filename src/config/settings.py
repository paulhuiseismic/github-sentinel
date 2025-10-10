"""
GitHub Sentinel 配置管理
"""
import os
import yaml
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
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
class LLMProviderConfig:
    """LLM 提供商配置"""
    name: str
    type: str  # "azure_openai", "openai"
    model_name: str
    api_key: str
    azure_endpoint: Optional[str] = None
    api_version: Optional[str] = "2024-02-15-preview"
    is_default: bool = False
    max_tokens: int = 2000
    temperature: float = 0.7
    top_p: float = 1.0
    frequency_penalty: float = 0
    presence_penalty: float = 0


@dataclass
class ReportConfig:
    """报告生成配置"""
    daily_progress_dir: str = "daily_progress"
    reports_dir: str = "data/reports"
    default_template: str = "github_azure_prompt.txt"
    templates_dir: str = "prompts"
    output_formats: List[str] = field(default_factory=lambda: ["markdown", "json"])
    enable_llm_summary: bool = True
    batch_size: int = 5
    retry_attempts: int = 3


@dataclass
class DatabaseConfig:
    """数据库配置"""
    url: str = "sqlite:///github_sentinel.db"
    path: str = "data/subscriptions.json"  # 添加path属性用于JSON文件存储
    echo: bool = False


@dataclass
class SchedulerConfig:
    """调度器配置"""
    enabled: bool = True
    daily_report_time: str = "09:00"
    timezone: str = "UTC"
    max_workers: int = 4


@dataclass
class NotificationConfig:
    """通知配置"""
    enabled: bool = False
    email_enabled: bool = False
    smtp_server: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    recipients: List[str] = field(default_factory=list)


@dataclass
class Settings:
    """主配置类"""
    github: GitHubConfig
    llm_providers: List[LLMProviderConfig] = field(default_factory=list)
    notification: NotificationConfig = field(default_factory=NotificationConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    report: ReportConfig = field(default_factory=ReportConfig)
    log_level: str = "INFO"
    log_file: str = "logs/github_sentinel.log"
    daily_scan_time: str = "09:00"
    weekly_scan_time: str = "09:00"
    weekly_scan_day: str = "monday"
    max_concurrent_requests: int = 5

    @classmethod
    def from_config_file(cls, config_path: Optional[str] = None) -> "Settings":
        """从配置文件创建设置"""
        # 默认配置文件路径
        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"

        config_data = {}
        if Path(config_path).exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f) or {}

        # 处理GitHub配置 - 优先从环境变量获取token
        github_config = config_data.get("github", {})
        github_token = os.getenv("GITHUB_TOKEN") or github_config.get("token")

        if not github_token or github_token == "null" or github_token is None:
            # 尝试从其他可能的环境变量获取
            github_token = (
                os.getenv("GH_TOKEN") or
                os.getenv("GITHUB_ACCESS_TOKEN") or
                ""
            )

        github = GitHubConfig(
            token=github_token,
            api_url=github_config.get("api_url", "https://api.github.com"),
            rate_limit_per_hour=github_config.get("rate_limit_per_hour", 5000),
            timeout=github_config.get("timeout", 30)
        )

        # LLM 提供商配置
        llm_providers = []

        # Azure OpenAI 配置
        if os.getenv("AZURE_OPENAI_API_KEY"):
            azure_provider = LLMProviderConfig(
                name="azure_openai",
                type="azure_openai",
                model_name=os.getenv("AZURE_OPENAI_MODEL", "gpt-4"),
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
                is_default=True
            )
            llm_providers.append(azure_provider)

        # OpenAI 配置
        if os.getenv("OPENAI_API_KEY"):
            openai_provider = LLMProviderConfig(
                name="openai",
                type="openai",
                model_name=os.getenv("OPENAI_MODEL", "gpt-4"),
                api_key=os.getenv("OPENAI_API_KEY"),
                is_default=len(llm_providers) == 0  # 如果没有其他提供商则设为默认
            )
            llm_providers.append(openai_provider)

        notification = NotificationConfig(
            enabled=config_data.get("notification", {}).get("enabled", False),
            email_enabled=config_data.get("notification", {}).get("email_enabled", False),
            smtp_server=config_data.get("notification", {}).get("smtp_server", ""),
            smtp_port=config_data.get("notification", {}).get("smtp_port", 587),
            smtp_username=config_data.get("notification", {}).get("smtp_username", ""),
            smtp_password=config_data.get("notification", {}).get("smtp_password", ""),
            recipients=config_data.get("notification", {}).get("recipients", [])
        )

        database = DatabaseConfig(
            url=config_data.get("database", {}).get("url", "sqlite:///github_sentinel.db"),
            path=config_data.get("database", {}).get("path", "data/subscriptions.json"),  # 添加path属性用于JSON文件存储
            echo=config_data.get("database", {}).get("echo", False)
        )

        report = ReportConfig(
            daily_progress_dir=config_data.get("report", {}).get("daily_progress_dir", "daily_progress"),
            reports_dir=config_data.get("report", {}).get("reports_dir", "data/reports"),
            default_template=config_data.get("report", {}).get("default_template", "github_azure_prompt.txt"),
            templates_dir=config_data.get("report", {}).get("templates_dir", "prompts"),
            output_formats=config_data.get("report", {}).get("output_formats", ["markdown", "json"]),
            enable_llm_summary=config_data.get("report", {}).get("enable_llm_summary", True),
            batch_size=config_data.get("report", {}).get("batch_size", 5),
            retry_attempts=config_data.get("report", {}).get("retry_attempts", 3)
        )

        return cls(
            github=github,
            llm_providers=llm_providers,
            notification=notification,
            database=database,
            report=report,
            log_level=config_data.get("log_level", "INFO"),
            log_file=config_data.get("log_file", "logs/github_sentinel.log"),
            daily_scan_time=config_data.get("daily_scan_time", "09:00"),
            weekly_scan_time=config_data.get("weekly_scan_time", "09:00"),
            weekly_scan_day=config_data.get("weekly_scan_day", "monday"),
            max_concurrent_requests=config_data.get("max_concurrent_requests", 5)
        )

    @classmethod
    def from_env(cls) -> "Settings":
        """从环境变量加载设置"""
        github_config = GitHubConfig(
            token=os.getenv("GITHUB_TOKEN", ""),
            api_url=os.getenv("GITHUB_API_URL", "https://api.github.com"),
            rate_limit_per_hour=int(os.getenv("GITHUB_RATE_LIMIT", "5000")),
            timeout=int(os.getenv("GITHUB_TIMEOUT", "30"))
        )

        # LLM 提供商配置
        llm_providers = []

        # Azure OpenAI 配置
        if os.getenv("AZURE_OPENAI_API_KEY"):
            azure_provider = LLMProviderConfig(
                name="azure_openai",
                type="azure_openai",
                model_name=os.getenv("AZURE_OPENAI_MODEL", "gpt-4"),
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
                is_default=True
            )
            llm_providers.append(azure_provider)

        # OpenAI 配置
        if os.getenv("OPENAI_API_KEY"):
            openai_provider = LLMProviderConfig(
                name="openai",
                type="openai",
                model_name=os.getenv("OPENAI_MODEL", "gpt-4"),
                api_key=os.getenv("OPENAI_API_KEY"),
                is_default=len(llm_providers) == 0  # 如果没有其他提供商则设为默认
            )
            llm_providers.append(openai_provider)

        return cls(
            github=github_config,
            llm_providers=llm_providers,
            debug=os.getenv("DEBUG", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "Settings":
        """从字典创建设置对象"""
        # GitHub 配置
        github_data = data.get("github", {})
        github_config = GitHubConfig(
            token=github_data.get("token", os.getenv("GITHUB_TOKEN", "")),
            api_url=github_data.get("api_url", "https://api.github.com"),
            rate_limit_per_hour=github_data.get("rate_limit_per_hour", 5000),
            timeout=github_data.get("timeout", 30)
        )

        # LLM 提供商配置
        llm_providers = []
        for provider_data in data.get("llm_providers", []):
            provider = LLMProviderConfig(
                name=provider_data["name"],
                type=provider_data["type"],
                model_name=provider_data["model_name"],
                api_key=provider_data.get("api_key", ""),
                azure_endpoint=provider_data.get("azure_endpoint"),
                api_version=provider_data.get("api_version", "2024-02-15-preview"),
                is_default=provider_data.get("is_default", False),
                max_tokens=provider_data.get("max_tokens", 2000),
                temperature=provider_data.get("temperature", 0.7),
                top_p=provider_data.get("top_p", 1.0),
                frequency_penalty=provider_data.get("frequency_penalty", 0),
                presence_penalty=provider_data.get("presence_penalty", 0)
            )
            llm_providers.append(provider)

        # 报告配置
        report_data = data.get("report", {})
        report_config = ReportConfig(
            daily_progress_dir=report_data.get("daily_progress_dir", "daily_progress"),
            reports_dir=report_data.get("reports_dir", "data/reports"),
            default_template=report_data.get("default_template", "github_azure_prompt.txt"),
            templates_dir=report_data.get("templates_dir", "prompts"),
            output_formats=report_data.get("output_formats", ["markdown", "json"]),
            enable_llm_summary=report_data.get("enable_llm_summary", True),
            batch_size=report_data.get("batch_size", 5),
            retry_attempts=report_data.get("retry_attempts", 3)
        )

        # 其他配置...
        database_data = data.get("database", {})
        database_config = DatabaseConfig(
            url=database_data.get("url", "sqlite:///github_sentinel.db"),
            path=database_data.get("path", "data/subscriptions.json"),  # 添加path属性用于JSON文件存储
            echo=database_data.get("echo", False)
        )

        return cls(
            github=github_config,
            llm_providers=llm_providers,
            report=report_config,
            database=database_config,
            debug=data.get("debug", False),
            log_level=data.get("log_level", "INFO"),
            log_file=data.get("log_file", "logs/github_sentinel.log")
        )

    @classmethod
    def _create_default_config(cls, config_path: Path):
        """创建默认配置文件"""
        config_path.parent.mkdir(parents=True, exist_ok=True)

        default_config = {
            "github": {
                "token": "${GITHUB_TOKEN}",
                "api_url": "https://api.github.com",
                "rate_limit_per_hour": 5000,
                "timeout": 30
            },
            "llm_providers": [
                {
                    "name": "azure_openai",
                    "type": "azure_openai",
                    "model_name": "gpt-4",
                    "api_key": "${AZURE_OPENAI_API_KEY}",
                    "azure_endpoint": "${AZURE_OPENAI_ENDPOINT}",
                    "api_version": "2024-02-15-preview",
                    "is_default": True,
                    "max_tokens": 2000,
                    "temperature": 0.7
                }
            ],
            "report": {
                "daily_progress_dir": "daily_progress",
                "reports_dir": "data/reports",
                "default_template": "github_azure_prompt.txt",
                "templates_dir": "prompts",
                "output_formats": ["markdown", "json"],
                "enable_llm_summary": True,
                "batch_size": 5,
                "retry_attempts": 3
            },
            "database": {
                "url": "sqlite:///github_sentinel.db",
                "path": "data/subscriptions.json",  # 添加path属性用于JSON文件存储
                "echo": False
            },
            "scheduler": {
                "enabled": True,
                "daily_report_time": "09:00",
                "timezone": "UTC",
                "max_workers": 4
            },
            "notification": {
                "enabled": False,
                "email_enabled": False
            },
            "debug": False,
            "log_level": "INFO",
            "log_file": "logs/github_sentinel.log"
        }

        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True, indent=2)

    def get_default_llm_provider(self) -> Optional[LLMProviderConfig]:
        """获取默认LLM提供商配置"""
        for provider in self.llm_providers:
            if provider.is_default:
                return provider
        return self.llm_providers[0] if self.llm_providers else None

    def get_llm_provider(self, name: str) -> Optional[LLMProviderConfig]:
        """根据名称获取LLM提供商配置"""
        for provider in self.llm_providers:
            if provider.name == name:
                return provider
        return None
