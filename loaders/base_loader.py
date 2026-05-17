"""
文档加载器基类
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
import os


class BaseLoader(ABC):
    """文档加载器抽象基类"""
    
    def __init__(self, file_path: str):
        """
        初始化加载器
        
        Args:
            file_path: 文档路径
        """
        self.file_path = file_path
        self._validate_file()
    
    def _validate_file(self):
        """验证文件是否存在且可读"""
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"文件不存在: {self.file_path}")
        
        if not os.path.isfile(self.file_path):
            raise ValueError(f"不是有效的文件: {self.file_path}")
    
    @abstractmethod
    def load(self) -> str:
        """
        加载文档内容
        
        Returns:
            str: 文档的文本内容
        """
        pass
    
    @abstractmethod
    def load_with_metadata(self) -> List[Dict[str, Any]]:
        """
        加载文档内容及元数据
        
        Returns:
            List[Dict[str, Any]]: 包含内容和元数据的列表
            每个元素包含: {'content': str, 'metadata': dict}
        """
        pass
    
    def get_file_info(self) -> Dict[str, Any]:
        """
        获取文件基本信息
        
        Returns:
            Dict[str, Any]: 文件信息
        """
        stat = os.stat(self.file_path)
        _, ext = os.path.splitext(self.file_path)
        
        return {
            'file_name': os.path.basename(self.file_path),
            'file_path': self.file_path,
            'file_size': stat.st_size,
            'file_extension': ext.lower(),
            'file_type': self._get_file_type(),
        }
    
    @abstractmethod
    def _get_file_type(self) -> str:
        """获取文件类型描述"""
        pass
