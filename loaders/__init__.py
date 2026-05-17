"""
文档加载器模块
支持多种文档格式的加载和解析
"""

from .base_loader import BaseLoader
from .pdf_loader import PDFLoader
from .docx_loader import DocxLoader
from .md_loader import MarkdownLoader
from .txt_loader import TextLoader

__all__ = [
    'BaseLoader',
    'PDFLoader',
    'DocxLoader',
    'MarkdownLoader',
    'TextLoader',
    'get_loader'
]


def get_loader(file_path: str):
    """
    根据文件扩展名返回对应的加载器
    
    Args:
        file_path: 文件路径
        
    Returns:
        BaseLoader: 对应的文档加载器实例
        
    Raises:
        ValueError: 不支持的文件格式
    """
    import os
    _, ext = os.path.splitext(file_path.lower())
    
    loaders = {
        '.pdf': PDFLoader,
        '.docx': DocxLoader,
        '.doc': DocxLoader,  # 尝试用python-docx打开.doc
        '.md': MarkdownLoader,
        '.markdown': MarkdownLoader,
        '.txt': TextLoader,
        '.text': TextLoader,
    }
    
    if ext not in loaders:
        raise ValueError(f"不支持的文件格式: {ext}")
    
    return loaders[ext](file_path)
