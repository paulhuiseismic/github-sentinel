"""
LLM 服务模块 - 支持多种 LLM 提供商
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from pathlib import Path

try:
    from openai import AsyncAzureOpenAI
    AZURE_OPENAI_AVAILABLE = True
except ImportError:
    AZURE_OPENAI_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class BaseLLMProvider(ABC):
    """LLM 提供商基类"""

    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    async def generate_completion(self, prompt: str, **kwargs) -> str:
        """生成文本完成"""
        pass

    @abstractmethod
    async def generate_chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """生成对话完成"""
        pass


class AzureOpenAIProvider(BaseLLMProvider):
    """Azure OpenAI 提供商"""

    def __init__(self,
                 model_name: str,
                 api_key: str,
                 azure_endpoint: str,
                 api_version: str = "2024-02-15-preview",
                 **kwargs):
        super().__init__(model_name, **kwargs)

        if not AZURE_OPENAI_AVAILABLE:
            raise ImportError("请安装 openai 包: pip install openai")

        self.client = AsyncAzureOpenAI(
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version
        )

    async def generate_completion(self, prompt: str, **kwargs) -> str:
        """生成文本完成"""
        try:
            response = await self.client.completions.create(
                model=self.model_name,
                prompt=prompt,
                max_tokens=kwargs.get('max_tokens', 8000),
                temperature=kwargs.get('temperature', 0.7),
                top_p=kwargs.get('top_p', 1.0),
                frequency_penalty=kwargs.get('frequency_penalty', 0),
                presence_penalty=kwargs.get('presence_penalty', 0),
            )
            return response.choices[0].text.strip()
        except Exception as e:
            self.logger.error(f"Azure OpenAI completion 生成失败: {str(e)}")
            raise

    async def generate_chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """生成对话完成"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=kwargs.get('max_tokens', 8000),
                temperature=kwargs.get('temperature', 0.7),
                top_p=kwargs.get('top_p', 1.0),
                frequency_penalty=kwargs.get('frequency_penalty', 0),
                presence_penalty=kwargs.get('presence_penalty', 0),
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            self.logger.error(f"Azure OpenAI chat completion 生成失败: {str(e)}")
            raise


class OpenAIProvider(BaseLLMProvider):
    """OpenAI 提供商"""

    def __init__(self,
                 model_name: str,
                 api_key: str,
                 **kwargs):
        super().__init__(model_name, **kwargs)

        if not OPENAI_AVAILABLE:
            raise ImportError("请安装 openai 包: pip install openai")

        self.client = openai.AsyncOpenAI(api_key=api_key)

    async def generate_completion(self, prompt: str, **kwargs) -> str:
        """生成文本完成"""
        try:
            response = await self.client.completions.create(
                model=self.model_name,
                prompt=prompt,
                max_tokens=kwargs.get('max_tokens', 8000),
                temperature=kwargs.get('temperature', 0.7),
                top_p=kwargs.get('top_p', 1.0),
                frequency_penalty=kwargs.get('frequency_penalty', 0),
                presence_penalty=kwargs.get('presence_penalty', 0),
            )
            return response.choices[0].text.strip()
        except Exception as e:
            self.logger.error(f"OpenAI completion 生成失败: {str(e)}")
            raise

    async def generate_chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """生成对话完成"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=kwargs.get('max_tokens', 8000),
                temperature=kwargs.get('temperature', 0.7),
                top_p=kwargs.get('top_p', 1.0),
                frequency_penalty=kwargs.get('frequency_penalty', 0),
                presence_penalty=kwargs.get('presence_penalty', 0),
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            self.logger.error(f"OpenAI chat completion 生成失败: {str(e)}")
            raise


class LLMService:
    """LLM 服务管理类"""

    def __init__(self):
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.default_provider = None
        self.logger = logging.getLogger(__name__)

    def add_provider(self, name: str, provider: BaseLLMProvider, is_default: bool = False):
        """添加 LLM 提供商"""
        self.providers[name] = provider
        if is_default or not self.default_provider:
            self.default_provider = name
        self.logger.info(f"已添加 LLM 提供商: {name}")

    def get_provider(self, name: Optional[str] = None) -> BaseLLMProvider:
        """获取 LLM 提供商"""
        provider_name = name or self.default_provider
        if not provider_name or provider_name not in self.providers:
            raise ValueError(f"LLM 提供商不存在: {provider_name}")
        return self.providers[provider_name]

    async def generate_text(self, prompt: str, provider_name: Optional[str] = None, **kwargs) -> str:
        """生成文本"""
        provider = self.get_provider(provider_name)
        return await provider.generate_completion(prompt, **kwargs)

    async def generate_chat(self, messages: List[Dict[str, str]],
                           provider_name: Optional[str] = None, **kwargs) -> str:
        """生成对话"""
        provider = self.get_provider(provider_name)
        return await provider.generate_chat_completion(messages, **kwargs)

    async def generate_report_from_template(self,
                                          template_path: str,
                                          markdown_content: str,
                                          provider_name: Optional[str] = None,
                                          **kwargs) -> str:
        """使用模板生成报告"""
        # 读取模板
        template_file = Path(template_path)
        if not template_file.exists():
            raise FileNotFoundError(f"模板文件不存在: {template_path}")

        with open(template_file, 'r', encoding='utf-8') as f:
            template = f.read()

        # 构建消息
        messages = [
            {
                "role": "system",
                "content": template
            },
            {
                "role": "user",
                "content": markdown_content
            }
        ]

        # 生成报告
        return await self.generate_chat(messages, provider_name, **kwargs)

    async def generate_summary_report(self,
                                     repo_name: str,
                                     markdown_content: str,
                                     template_name: str = "github_azure_prompt.txt",
                                     provider_name: Optional[str] = None,
                                     output_dir: str = "daily_progress",
                                     **kwargs) -> str:
        """生成项目摘要报告"""
        # 构建模板路径
        template_path = Path("prompts") / template_name

        # 生成报告内容
        report_content = await self.generate_report_from_template(
            str(template_path), markdown_content, provider_name, **kwargs
        )

        # 保存报告
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{repo_name}_summary_{timestamp}.md"
        filepath = output_path / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)

        self.logger.info(f"摘要报告已生成: {filepath}")
        return str(filepath)

    def list_providers(self) -> List[str]:
        """列出所有可用的提供商"""
        return list(self.providers.keys())

    def get_provider_info(self, name: str) -> Dict[str, Any]:
        """获取提供商信息"""
        if name not in self.providers:
            raise ValueError(f"提供商不存在: {name}")

        provider = self.providers[name]
        return {
            "name": name,
            "model": provider.model_name,
            "type": provider.__class__.__name__,
            "is_default": name == self.default_provider
        }


def create_azure_openai_provider(config: Dict[str, Any]) -> AzureOpenAIProvider:
    """创建 Azure OpenAI 提供商"""
    return AzureOpenAIProvider(
        model_name=config['model_name'],
        api_key=config['api_key'],
        azure_endpoint=config['azure_endpoint'],
        api_version=config.get('api_version', '2024-02-15-preview')
    )


def create_openai_provider(config: Dict[str, Any]) -> OpenAIProvider:
    """创建 OpenAI 提供商"""
    return OpenAIProvider(
        model_name=config['model_name'],
        api_key=config['api_key']
    )
