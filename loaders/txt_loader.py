"""
纯文本文档加载器
"""

import os
from typing import List, Dict, Any
from .base_loader import BaseLoader


class TextLoader(BaseLoader):
    """纯文本文档加载器"""
    
    def __init__(self, file_path: str):
        """
        初始化文本加载器
        
        Args:
            file_path: 文本文件路径
        """
        super().__init__(file_path)
        self.encoding = self._detect_encoding()
    
    def _detect_encoding(self) -> str:
        """
        检测文件编码
        
        Returns:
            str: 检测到的编码
        """
        # 尝试常见的编码
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1', 'cp1252', 'utf-16']
        
        for encoding in encodings:
            try:
                with open(self.file_path, 'r', encoding=encoding) as f:
                    f.read(1024)  # 只读前1024个字符进行测试
                return encoding
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        # 如果都失败了，使用chardet检测
        try:
            import chardet
            with open(self.file_path, 'rb') as f:
                raw_data = f.read(10000)  # 读前10KB
            result = chardet.detect(raw_data)
            if result and result['confidence'] > 0.7:
                return result['encoding']
        except ImportError:
            pass
        
        # 默认返回utf-8，忽略错误
        return 'utf-8'
    
    def load(self) -> str:
        """
        加载文本文档内容
        
        Returns:
            str: 文本文档的内容
        """
        try:
            with open(self.file_path, 'r', encoding=self.encoding, errors='ignore') as f:
                content = f.read()
            return content
        except Exception as e:
            raise RuntimeError(f"读取文本文件失败: {str(e)}")
    
    def load_with_metadata(self) -> List[Dict[str, Any]]:
        """
        加载文本内容及元数据
        
        Returns:
            List[Dict[str, Any]]: 按段落分割的内容和元数据
        """
        content = self.load()
        
        # 按段落分割（空行分割）
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        documents = []
        for idx, paragraph in enumerate(paragraphs):
            documents.append({
                'content': paragraph,
                'metadata': {
                    'source': self.file_path,
                    'file_name': os.path.basename(self.file_path),
                    'paragraph_index': idx,
                    'encoding': self.encoding,
                }
            })
        
        # 如果文档没有段落分割，则返回整个文档
        if not documents:
            documents.append({
                'content': content,
                'metadata': {
                    'source': self.file_path,
                    'file_name': os.path.basename(self.file_path),
                    'paragraph_index': 0,
                    'encoding': self.encoding,
                }
            })
        
        return documents
    
    def _get_file_type(self) -> str:
        """获取文件类型描述"""
        return "纯文本文档"
    
    def get_text_info(self) -> Dict[str, Any]:
        """
        获取文本文档信息
        
        Returns:
            Dict[str, Any]: 文档信息
        """
        content = self.load()
        
        # 统计信息
        lines = content.split('\n')
        paragraphs = [p for p in content.split('\n\n') if p.strip()]
        words = content.split()
        
        info = {
            'file_name': os.path.basename(self.file_path),
            'file_size': os.path.getsize(self.file_path),
            'encoding': self.encoding,
            'total_characters': len(content),
            'total_characters_no_spaces': len(content.replace(' ', '').replace('\n', '').replace('\t', '')),
            'total_words': len(words),
            'total_lines': len(lines),
            'total_paragraphs': len(paragraphs),
        }
        
        return info
