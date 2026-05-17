"""
处理器工厂
根据配置创建相应的LLM处理器
"""

from typing import Dict, Any
from .base_processor import BaseProcessor
from .openai_processor import OpenAIProcessor
from .ollama_processor import OllamaProcessor
from .deepseek_processor import DeepSeekProcessor


class ProcessorFactory:
    """LLM处理器工厂类"""
    
    # 注册的处理器类
    _processors = {
        'openai': OpenAIProcessor,
        'ollama': OllamaProcessor,
        'deepseek': DeepSeekProcessor,
    }
    
    @classmethod
    def create(cls, provider: str = None, config: Dict[str, Any] = None) -> BaseProcessor:
        """
        创建LLM处理器实例
        
        Args:
            provider: 提供商名称 ('openai', 'ollama')
            config: 配置字典（如果为None，则从默认配置文件读取）
            
        Returns:
            BaseProcessor: LLM处理器实例
            
        Raises:
            ValueError: 不支持的提供商或配置错误
        """
        # 如果未提供配置，则加载默认配置
        if config is None:
            config = cls._load_default_config()
        
        # 如果未指定provider，则使用配置中的默认provider
        if provider is None:
            provider = config.get('llm', {}).get('provider', 'openai')
        
        provider = provider.lower()
        
        # 获取提供商的配置
        provider_config = config.get('llm', {}).get(provider, {})
        
        # 合并通用配置
        general_config = {
            'temperature': config.get('llm', {}).get('temperature', 0.3),
            'max_tokens': config.get('llm', {}).get('max_tokens', 4096),
            'stream': config.get('llm', {}).get('stream', False),
        }
        provider_config.update(general_config)
        
        # 添加prompts配置
        if 'prompts' in config.get('wiki', {}):
            provider_config['prompts'] = config['wiki']['prompts']
        
        # 创建处理器实例
        if provider not in cls._processors:
            raise ValueError(
                f"不支持的LLM提供商: {provider}。"
                f"支持的提供商: {list(cls._processors.keys())}"
            )
        
        try:
            processor_class = cls._processors[provider]
            return processor_class(provider_config)
        except Exception as e:
            raise RuntimeError(f"创建{provider}处理器失败: {str(e)}")
    
    @classmethod
    def register_processor(cls, name: str, processor_class: type):
        """
        注册自定义处理器
        
        Args:
            name: 处理器名称
            processor_class: 处理器类（必须继承自BaseProcessor）
        """
        if not issubclass(processor_class, BaseProcessor):
            raise ValueError("处理器类必须继承自BaseProcessor")
        
        cls._processors[name.lower()] = processor_class
    
    @classmethod
    def list_processors(cls) -> list:
        """
        列出所有可用的处理器
        
        Returns:
            list: 处理器名称列表
        """
        return list(cls._processors.keys())
    
    @staticmethod
    def _load_default_config() -> Dict[str, Any]:
        """
        加载默认配置文件
        
        Returns:
            Dict[str, Any]: 配置字典
            
        Raises:
            FileNotFoundError: 配置文件不存在
            yaml.YAMLError: 配置文件格式错误
        """
        import os
        import yaml
        
        # 配置文件的默认路径
        config_paths = [
            'config/config.yaml',  # 当前目录下的config文件夹
            '../config/config.yaml',  # 上级目录
            os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml'),
        ]
        
        config_file = None
        for path in config_paths:
            if os.path.exists(path):
                config_file = path
                break
        
        if config_file is None:
            raise FileNotFoundError(
                "未找到配置文件config.yaml。"
                "请确保配置文件存在于config/目录下。"
            )
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"配置文件格式错误: {str(e)}")
