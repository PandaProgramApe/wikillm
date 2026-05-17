"""
DeepSeek API 处理器
DeepSeek API 完全兼容 OpenAI SDK，继承 OpenAIProcessor 并指向 DeepSeek 官方端点。
获取 API Key: https://platform.deepseek.com

支持的 V4 模型:
  - deepseek-v4: 旗舰多模态 MoE 模型（推荐）
  - deepseek-v4-flash: 低延迟变体，适合实时对话和高吞吐
  - deepseek-v4-pro: 高推理变体，适合复杂分析和长文本输出
"""

import os
from typing import List, Dict, Any
from .openai_processor import OpenAIProcessor


class DeepSeekProcessor(OpenAIProcessor):
    """
    DeepSeek API 处理器
    兼容 OpenAI SDK，但完全覆盖 api_key 获取逻辑，避免误用 OpenAI 的 key。
    """

    DEFAULT_BASE_URL = "https://api.deepseek.com"
    DEFAULT_MODEL = "deepseek-v4"

    # DeepSeek 支持的 V4 模型列表
    SUPPORTED_MODELS = [
        "deepseek-v4",          # 旗舰多模态 MoE
        "deepseek-v4-flash",    # 低延迟变体
        "deepseek-v4-pro",      # 高推理变体
        # 兼容旧模型（2026/07/24 废弃）
        "deepseek-chat",
        "deepseek-reasoner",
    ]

    def __init__(self, config: Dict[str, Any]):
        """
        初始化 DeepSeek 处理器

        Args:
            config: 配置字典，包含 api_key, model, base_url 等
        """
        # 深拷贝 config 避免污染原字典
        config = dict(config)

        # 设置 DeepSeek 专属默认值
        if not config.get('base_url'):
            config['base_url'] = self.DEFAULT_BASE_URL

        # --- 关键修复：只从 DEEPSEEK_API_KEY 读取 key，绝不回退到 OPENAI_API_KEY ---
        api_key = config.get('api_key') or os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            raise ValueError(
                "DeepSeek API密钥未配置。"
                "请在config.yaml的deepseek.api_key中设置，"
                "或在环境变量DEEPSEEK_API_KEY中设置。"
                "获取API Key: https://platform.deepseek.com"
            )
        config['api_key'] = api_key

        # 设置默认模型为 V4
        if not config.get('model') or config.get('model') == 'gpt-4o-mini':
            config['model'] = self.DEFAULT_MODEL

        # 调用父类 OpenAIProcessor.__init__
        super().__init__(config)

    def get_provider_name(self) -> str:
        return "deepseek"

    @classmethod
    def list_models(cls) -> list:
        """列出支持的模型"""
        return cls.SUPPORTED_MODELS
