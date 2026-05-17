"""
Word文档加载器
使用python-docx加载DOCX文件
"""

import os
from typing import List, Dict, Any
from .base_loader import BaseLoader


class DocxLoader(BaseLoader):
    """Word文档加载器（支持.docx和.doc）"""
    
    def __init__(self, file_path: str):
        """
        初始化Word文档加载器
        
        Args:
            file_path: Word文档路径
        """
        super().__init__(file_path)
        self._check_dependencies()
    
    def _check_dependencies(self):
        """检查依赖库是否已安装"""
        try:
            import docx  # noqa: F401
        except ImportError:
            raise ImportError(
                "Word文档加载需要python-docx库。请运行: pip install python-docx"
            )
    
    def load(self) -> str:
        """
        加载Word文档内容
        
        Returns:
            str: Word文档的文本内容
        """
        import docx
        
        try:
            doc = docx.Document(self.file_path)
            
            # 提取所有段落文本
            paragraphs = []
            for para in doc.paragraphs:
                if para.text.strip():
                    paragraphs.append(para.text)
            
            # 提取表格内容
            tables_text = []
            for table in doc.tables:
                for row in table.rows:
                    row_text = [cell.text.strip() for cell in row.cells]
                    if any(row_text):
                        tables_text.append(" | ".join(row_text))
            
            # 合并文本
            all_text = "\n\n".join(paragraphs)
            if tables_text:
                all_text += "\n\n## 表格内容\n\n" + "\n\n".join(tables_text)
            
            return all_text
            
        except Exception as e:
            raise RuntimeError(f"读取Word文档失败: {str(e)}")
    
    def load_with_metadata(self) -> List[Dict[str, Any]]:
        """
        加载Word文档内容及元数据
        
        Returns:
            List[Dict[str, Any]]: 段落级别的内容和元数据
        """
        import docx
        
        documents = []
        
        try:
            doc = docx.Document(self.file_path)
            
            # 获取核心属性
            core_props = doc.core_properties
            
            # 按段落分割
            for idx, para in enumerate(doc.paragraphs):
                if para.text.strip():
                    documents.append({
                        'content': para.text,
                        'metadata': {
                            'source': self.file_path,
                            'file_name': os.path.basename(self.file_path),
                            'paragraph_index': idx,
                            'paragraph_style': para.style.name if para.style else '',
                            'core_properties': {
                                'title': core_props.title,
                                'author': core_props.author,
                                'created': str(core_props.created) if core_props.created else '',
                                'modified': str(core_props.modified) if core_props.modified else '',
                            }
                        }
                    })
            
            # 如果有表格，也加入
            for table_idx, table in enumerate(doc.tables):
                table_content = []
                for row in table.rows:
                    row_text = [cell.text.strip() for cell in row.cells]
                    table_content.append(" | ".join(row_text))
                
                if table_content:
                    documents.append({
                        'content': "\n".join(table_content),
                        'metadata': {
                            'source': self.file_path,
                            'file_name': os.path.basename(self.file_path),
                            'type': 'table',
                            'table_index': table_idx,
                        }
                    })
            
        except Exception as e:
            raise RuntimeError(f"读取Word文档失败: {str(e)}")
        
        return documents
    
    def _get_file_type(self) -> str:
        """获取文件类型描述"""
        _, ext = os.path.splitext(self.file_path.lower())
        if ext == '.docx':
            return "Word文档 (.docx)"
        else:
            return "Word文档 (.doc)"
    
    def get_docx_info(self) -> Dict[str, Any]:
        """
        获取Word文档详细信息
        
        Returns:
            Dict[str, Any]: 文档元数据
        """
        import docx
        
        try:
            doc = docx.Document(self.file_path)
            core_props = doc.core_properties
            
            info = {
                'title': core_props.title,
                'author': core_props.author,
                'comments': core_props.comments,
                'created': str(core_props.created) if core_props.created else '',
                'modified': str(core_props.modified) if core_props.modified else '',
                'last_modified_by': core_props.last_modified_by,
                'revision': core_props.revision,
                'paragraph_count': len(doc.paragraphs),
                'table_count': len(doc.tables),
                'file_size': os.path.getsize(self.file_path),
            }
            
            return info
            
        except Exception as e:
            raise RuntimeError(f"获取Word文档信息失败: {str(e)}")
