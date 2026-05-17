"""
PDF文档加载器
使用PyMuPDF (fitz) 加载PDF文件
"""

import os
from typing import List, Dict, Any
from .base_loader import BaseLoader


class PDFLoader(BaseLoader):
    """PDF文档加载器"""
    
    def __init__(self, file_path: str):
        """
        初始化PDF加载器
        
        Args:
            file_path: PDF文件路径
        """
        super().__init__(file_path)
        self._check_dependencies()
    
    def _check_dependencies(self):
        """检查依赖库是否已安装"""
        try:
            import pymupdf  # noqa: F401
        except ImportError:
            try:
                import fitz  # noqa: F401
            except ImportError:
                raise ImportError(
                    "PDF加载需要PyMuPDF库。请运行: pip install pymupdf"
                )
    
    def load(self) -> str:
        """
        加载PDF文档内容
        
        Returns:
            str: PDF的文本内容
        """
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz
        
        text_content = []
        
        try:
            doc = fitz.open(self.file_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    text_content.append(f"## 第 {page_num + 1} 页\n\n{text}")
            
            doc.close()
            
        except Exception as e:
            raise RuntimeError(f"读取PDF文件失败: {str(e)}")
        
        return "\n\n".join(text_content)
    
    def load_with_metadata(self) -> List[Dict[str, Any]]:
        """
        加载PDF内容及元数据
        
        Returns:
            List[Dict[str, Any]]: 每页的内容和元数据
        """
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz
        
        documents = []
        
        try:
            doc = fitz.open(self.file_path)
            metadata = doc.metadata
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                if text.strip():
                    documents.append({
                        'content': text,
                        'metadata': {
                            'source': self.file_path,
                            'file_name': os.path.basename(self.file_path),
                            'page': page_num + 1,
                            'total_pages': len(doc),
                            'pdf_metadata': metadata,
                        }
                    })
            
            doc.close()
            
        except Exception as e:
            raise RuntimeError(f"读取PDF文件失败: {str(e)}")
        
        return documents
    
    def _get_file_type(self) -> str:
        """获取文件类型描述"""
        return "PDF文档"
    
    def get_pdf_info(self) -> Dict[str, Any]:
        """
        获取PDF文件详细信息
        
        Returns:
            Dict[str, Any]: PDF元数据
        """
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz
        
        try:
            doc = fitz.open(self.file_path)
            metadata = doc.metadata
            
            info = {
                'title': metadata.get('title', ''),
                'author': metadata.get('author', ''),
                'subject': metadata.get('subject', ''),
                'keywords': metadata.get('keywords', ''),
                'creator': metadata.get('creator', ''),
                'producer': metadata.get('producer', ''),
                'creation_date': metadata.get('creationDate', ''),
                'modification_date': metadata.get('modDate', ''),
                'total_pages': len(doc),
                'file_size': os.path.getsize(self.file_path),
            }
            
            doc.close()
            return info
            
        except Exception as e:
            raise RuntimeError(f"获取PDF信息失败: {str(e)}")
