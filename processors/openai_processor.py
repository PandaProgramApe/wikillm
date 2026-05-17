"""
OpenAI API 处理器
支持OpenAI API和兼容的API（如Azure OpenAI、本地部署的OpenAI兼容API等）
"""

import os
from typing import List, Dict, Any
from .base_processor import BaseProcessor


class OpenAIProcessor(BaseProcessor):
    """OpenAI API处理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化OpenAI处理器
        
        Args:
            config: 配置字典，包含api_key, model, base_url等
        """
        super().__init__(config)
        
        # 获取API密钥（优先从参数，然后从环境变量）
        self.api_key = config.get('api_key') or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError(
                "OpenAI API密钥未配置。"
                "请在config.yaml中设置或在环境变量OPENAI_API_KEY中设置。"
            )
        
        self.base_url = config.get('base_url')
        self.model = config.get('model', 'gpt-4o-mini')
        
        # 初始化OpenAI客户端
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        except ImportError:
            raise ImportError(
                "使用OpenAI API需要安装openai库。"
                "请运行: pip install openai>=1.0.0"
            )
    
    def _call_api(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        调用OpenAI API（支持流式输出）

        Args:
            messages: 消息列表
            **kwargs: 其他参数，支持 stream=True 启用流式输出

        Returns:
            str: API响应内容
        """
        stream = kwargs.pop('stream', False)

        try:
            if stream:
                return self._call_api_streaming(messages, **kwargs)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get('temperature', self.temperature),
                max_tokens=kwargs.get('max_tokens', self.max_tokens),
                stream=False,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenAI API调用失败: {str(e)}")

    def _call_api_streaming(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        流式调用OpenAI API，实时输出生成内容

        Args:
            messages: 消息列表
            **kwargs: 其他参数

        Returns:
            str: API响应完整内容
        """
        collected = []
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get('temperature', self.temperature),
                max_tokens=kwargs.get('max_tokens', self.max_tokens),
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    print(delta.content, end='', flush=True)
                    collected.append(delta.content)
            print()  # 流式输出结束后换行
        except Exception as e:
            raise RuntimeError(f"OpenAI API流式调用失败: {str(e)}")
        return ''.join(collected)
    
    def analyze(self, content: str) -> str:
        """
        分析文档内容，提取关键信息

        Args:
            content: 文档内容

        Returns:
            str: 分析结果
        """
        prompt = self.config.get('prompts', {}).get('analyze', '')
        if not prompt:
            prompt = """
你是一个知识整理专家。请分析以下文档内容，提取关键信息：
1. 核心概念和定义
2. 主要论点和结论
3. 重要细节和示例
4. 章节结构和逻辑关系

文档内容：
{content}

请以结构化的方式输出分析结果。
"""

        prompt = prompt.replace('{content}', content)
        stream = self.config.get('stream', False)

        messages = [
            {"role": "system", "content": "你是一个专业的知识整理和分析专家。"},
            {"role": "user", "content": prompt}
        ]

        return self._call_api(messages, stream=stream)

    def compile(self, analysis: str) -> str:
        """
        将分析结果编译成Wiki文章

        Args:
            analysis: 分析结果

        Returns:
            str: 编译后的Wiki文章（Markdown格式）
        """
        prompt = self.config.get('prompts', {}).get('compile', '')
        if not prompt:
            prompt = """
你是一个Wiki编写专家。基于以下分析结果，编写一篇结构清晰、易于理解的Wiki文章：

分析结果：
{analysis}

要求：
1. 使用Markdown格式
2. 结构清晰，包含标题、子标题
3. 重要概念加粗
4. 添加适当的链接和引用
5. 语言简洁明了

请直接输出Wiki文章内容。
"""

        prompt = prompt.replace('{analysis}', analysis)
        stream = self.config.get('stream', False)

        messages = [
            {"role": "system", "content": "你是一个专业的Wiki编写专家。"},
            {"role": "user", "content": prompt}
        ]

        return self._call_api(messages, stream=stream)
    
    def query(self, question: str, context: str) -> str:
        """
        基于Wiki知识库回答问题
        
        Args:
            question: 用户问题
            context: 相关上下文/Wiki内容
            
        Returns:
            str: 回答
        """
        prompt = f"""
基于以下Wiki知识库内容，回答用户的问题。如果知识库中没有相关信息，请明确说明。

Wiki知识库内容：
{context}

用户问题：{question}

请提供准确、详细的回答，并引用知识库中的相关内容。
"""
        
        messages = [
            {"role": "system", "content": "你是一个知识库问答专家，基于提供的知识库内容回答用户问题。"},
            {"role": "user", "content": prompt}
        ]
        
        return self._call_api(messages)
    
    def summarize(self, content: str, max_length: int = 500) -> str:
        """
        总结内容
        
        Args:
            content: 要总结的内容
            max_length: 最大长度（字符数）
            
        Returns:
            str: 总结
        """
        # 如果内容本身就很短，直接返回
        if len(content) <= max_length:
            return content
        
        prompt = f"""
请对以下内容进行总结，总结长度控制在{max_length}字符以内。
保持关键信息和核心观点。

内容：
{content}

请直接输出总结，不要添加额外的解释。
"""
        
        messages = [
            {"role": "system", "content": "你是一个文本总结专家。"},
            {"role": "user", "content": prompt}
        ]
        
        summary = self._call_api(messages)
        
        # 如果总结还是太长，截断
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."
        
        return summary
