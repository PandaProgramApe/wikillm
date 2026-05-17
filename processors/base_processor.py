"""
LLM处理器基类
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseProcessor(ABC):
    """LLM处理器抽象基类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化处理器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.model = config.get('model', '')
        self.temperature = config.get('temperature', 0.3)
        self.max_tokens = config.get('max_tokens', 4096)
    
    @abstractmethod
    def analyze(self, content: str) -> str:
        """
        分析文档内容，提取关键信息
        
        Args:
            content: 文档内容
            
        Returns:
            str: 分析结果
        """
        pass
    
    @abstractmethod
    def compile(self, analysis: str) -> str:
        """
        将分析结果编译成Wiki文章
        
        Args:
            analysis: 分析结果
            
        Returns:
            str: 编译后的Wiki文章（Markdown格式）
        """
        pass
    
    @abstractmethod
    def query(self, question: str, context: str) -> str:
        """
        基于Wiki知识库回答问题
        
        Args:
            question: 用户问题
            context: 相关上下文/Wiki内容
            
        Returns:
            str: 回答
        """
        pass
    
    @abstractmethod
    def summarize(self, content: str, max_length: int = 500) -> str:
        """
        总结内容
        
        Args:
            content: 要总结的内容
            max_length: 最大长度（字符数）
            
        Returns:
            str: 总结
        """
        pass
    
    def chunk_text(self, text: str, chunk_size: int = 2000, overlap: int = 200) -> List[str]:
        """
        将长文本分块
        
        Args:
            text: 要分块的文本
            chunk_size: 每块的大小（字符数）
            overlap: 块之间的重叠（字符数）
            
        Returns:
            List[str]: 文本块列表
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # 尝试在句子边界分割
            if end < len(text):
                # 查找最后一个句号、问号或换行
                last_break = max(
                    text.rfind('。', start, end),
                    text.rfind('？', start, end),
                    text.rfind('\n', start, end),
                    text.rfind('. ', start, end),
                    text.rfind('? ', start, end),
                )
                if last_break != -1 and last_break > start + chunk_size // 2:
                    end = last_break + 1
            
            chunks.append(text[start:end])
            start = end - overlap if end - overlap > start else end
        
        return chunks
    
    def get_provider_name(self) -> str:
        """
        获取提供商名称
        
        Returns:
            str: 提供商名称
        """
        return self.__class__.__name__.replace('Processor', '').lower()
