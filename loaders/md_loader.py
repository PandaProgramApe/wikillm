"""
Markdown文档加载器
"""

import os
from typing import List, Dict, Any
from .base_loader import BaseLoader


class MarkdownLoader(BaseLoader):
    """Markdown文档加载器"""
    
    def load(self) -> str:
        """
        加载Markdown文档内容
        
        Returns:
            str: Markdown文档的文本内容
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except UnicodeDecodeError:
            # 尝试其他编码
            encodings = ['gbk', 'gb2312', 'latin-1', 'cp1252']
            for encoding in encodings:
                try:
                    with open(self.file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    return content
                except UnicodeDecodeError:
                    continue
            
            raise RuntimeError(f"无法解码文件: {self.file_path}")
        except Exception as e:
            raise RuntimeError(f"读取Markdown文件失败: {str(e)}")
    
    def load_with_metadata(self) -> List[Dict[str, Any]]:
        """
        加载Markdown内容及元数据
        
        Returns:
            List[Dict[str, Any]]: 按标题分割的内容和元数据
        """
        content = self.load()
        
        # 按Markdown标题分割内容
        import re
        documents = []
        
        # 使用正则表达式按标题分割
        # 匹配 # 到 #### 标题
        pattern = r'^(#{1,6}\s+.+)$'
        lines = content.split('\n')
        
        current_section = {'content': '', 'heading': 'Introduction'}
        
        for line in lines:
            if re.match(pattern, line.strip()):
                # 保存上一个section
                if current_section['content'].strip():
                    documents.append({
                        'content': current_section['content'].strip(),
                        'metadata': {
                            'source': self.file_path,
                            'file_name': os.path.basename(self.file_path),
                            'section': current_section['heading'],
                        }
                    })
                
                # 开始新section
                current_section = {'content': '', 'heading': line.strip()}
            else:
                current_section['content'] += line + '\n'
        
        # 添加最后一个section
        if current_section['content'].strip():
            documents.append({
                'content': current_section['content'].strip(),
                'metadata': {
                    'source': self.file_path,
                    'file_name': os.path.basename(self.file_path),
                    'section': current_section['heading'],
                }
            })
        
        # 如果没有按标题分割（文档没有标题），则返回整个文档
        if not documents:
            documents.append({
                'content': content,
                'metadata': {
                    'source': self.file_path,
                    'file_name': os.path.basename(self.file_path),
                    'section': 'Full Document',
                }
            })
        
        return documents
    
    def _get_file_type(self) -> str:
        """获取文件类型描述"""
        return "Markdown文档"
    
    def get_markdown_info(self) -> Dict[str, Any]:
        """
        获取Markdown文档信息
        
        Returns:
            Dict[str, Any]: 文档信息
        """
        content = self.load()
        
        import re
        
        # 统计标题
        headings = re.findall(r'^(#{1,6}\s+.+)$', content, re.MULTILINE)
        
        # 统计段落（空行分割）
        paragraphs = [p for p in content.split('\n\n') if p.strip()]
        
        info = {
            'file_name': os.path.basename(self.file_path),
            'file_size': os.path.getsize(self.file_path),
            'total_characters': len(content),
            'total_lines': len(content.split('\n')),
            'total_paragraphs': len(paragraphs),
            'total_headings': len(headings),
            'headings': headings[:10],  # 只显示前10个标题
        }
        
        return info
