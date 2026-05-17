"""
LLM处理器模块
支持多种LLM后端：OpenAI API、Ollama、DeepSeek等
"""

from .base_processor import BaseProcessor
from .openai_processor import OpenAIProcessor
from .ollama_processor import OllamaProcessor
from .deepseek_processor import DeepSeekProcessor
from .factory import ProcessorFactory

__all__ = [
    'BaseProcessor',
    'OpenAIProcessor',
    'OllamaProcessor',
    'DeepSeekProcessor',
    'ProcessorFactory',
    'get_processor',
]


def get_processor(provider: str = None, config: dict = None):
    """
    获取LLM处理器实例
    
    Args:
        provider: 提供商名称 ('openai', 'ollama', 'deepseek')
        config: 配置字典
        
    Returns:
        BaseProcessor: LLM处理器实例
    """
    return ProcessorFactory.create(provider, config)
