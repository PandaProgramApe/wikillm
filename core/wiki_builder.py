"""
Wiki构建器
负责将处理后的文档构建成结构化的Wiki知识库
"""

import os
import re
from typing import List, Dict, Any, Optional
from datetime import datetime


class WikiBuilder:
    """Wiki构建器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化Wiki构建器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.output_dir = config.get('wiki', {}).get('output_dir', 'data/wiki')
        os.makedirs(self.output_dir, exist_ok=True)
    
    def build_wiki(self, processed_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        构建Wiki知识库
        
        Args:
            processed_docs: 处理后的文档列表
            
        Returns:
            Dict[str, Any]: 构建结果
        """
        print(f"开始构建Wiki知识库，共 {len(processed_docs)} 个文档")
        
        # 1. 创建Wiki结构
        self._create_wiki_structure()
        
        # 2. 处理每个文档
        wiki_pages = []
        for doc in processed_docs:
            if 'error' in doc:
                print(f"跳过错误文档: {doc.get('source_file', 'unknown')}")
                continue
            
            wiki_page = self._create_wiki_page(doc)
            wiki_pages.append(wiki_page)
        
        # 3. 生成索引
        index_file = self._generate_index(wiki_pages)
        
        # 4. 生成导航
        nav_file = self._generate_navigation(wiki_pages)
        
        result = {
            'wiki_pages': wiki_pages,
            'index_file': index_file,
            'navigation_file': nav_file,
            'total_pages': len(wiki_pages),
            'output_dir': self.output_dir,
            'built_at': datetime.now().isoformat(),
        }
        
        print(f"Wiki知识库构建完成！共 {len(wiki_pages)} 个页面")
        print(f"索引文件: {index_file}")
        
        return result
    
    def _create_wiki_structure(self):
        """创建Wiki目录结构"""
        dirs = [
            self.output_dir,
            os.path.join(self.output_dir, 'concepts'),
            os.path.join(self.output_dir, 'details'),
            os.path.join(self.output_dir, 'summaries'),
        ]
        
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
    
    def _create_wiki_page(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建Wiki页面
        
        Args:
            doc: 处理后的文档信息
            
        Returns:
            Dict[str, Any]: Wiki页面信息
        """
        source_file = doc.get('source_file', '')
        wiki_content = doc.get('wiki_content', '')
        
        # 生成页面标题
        title = self._extract_title(wiki_content) or os.path.splitext(os.path.basename(source_file))[0]
        
        # 确定页面分类
        category = self._categorize_page(wiki_content)
        
        # 生成文件名
        file_name = self._generate_filename(title)
        file_path = os.path.join(self.output_dir, category, file_name)
        
        # 添加页面元数据
        page_content = self._add_page_metadata(doc, title, category)
        page_content += '\n\n' + wiki_content
        
        # 保存页面
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(page_content)
        
        page_info = {
            'title': title,
            'category': category,
            'file_path': file_path,
            'source_file': source_file,
            'characters': len(wiki_content),
        }
        
        print(f"  创建页面: {title} -> {file_path}")
        return page_info
    
    def _extract_title(self, content: str) -> Optional[str]:
        """
        从内容中提取标题
        
        Args:
            content: 文档内容
            
        Returns:
            Optional[str]: 标题，如果未找到则返回None
        """
        # 查找第一个一级或二级标题
        match = re.search(r'^#{1,2}\s+(.+)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return None
    
    def _categorize_page(self, content: str) -> str:
        """
        确定页面分类
        
        Args:
            content: 文档内容
            
        Returns:
            str: 分类名称 (concepts/details/summaries)
        """
        # 简单启发式分类
        content_lower = content.lower()
        
        # 检查是否主要是概念定义
        concept_keywords = ['定义', '概念', '是什么', 'definition', 'concept']
        if any(keyword in content_lower for keyword in concept_keywords):
            if len(content) < 2000:  # 短文本更可能是概念
                return 'concepts'
        
        # 检查是否主要是总结
        summary_keywords = ['总结', '摘要', '概述', 'summary', 'overview']
        if any(keyword in content_lower for keyword in summary_keywords):
            return 'summaries'
        
        # 默认归类为详细信息
        return 'details'
    
    def _generate_filename(self, title: str) -> str:
        """
        生成合法的文件名
        
        Args:
            title: 页面标题
            
        Returns:
            str: 文件名
        """
        # 移除或替换非法字符
        import re
        filename = re.sub(r'[<>:"/\\|?*]', '_', title)
        filename = filename.strip()
        
        # 限制长度
        if len(filename) > 100:
            filename = filename[:100]
        
        # 添加.md扩展名
        return filename + '.md'
    
    def _add_page_metadata(self, doc: Dict[str, Any], title: str, category: str) -> str:
        """
        添加页面元数据
        
        Args:
            doc: 文档信息
            title: 页面标题
            category: 页面分类
            
        Returns:
            str: 带元数据的页面内容
        """
        metadata = f"""---
title: {title}
category: {category}
source: {os.path.basename(doc.get('source_file', ''))}
processed_at: {doc.get('processed_at', datetime.now().isoformat())}
---

"""
        return metadata
    
    def _generate_index(self, wiki_pages: List[Dict[str, Any]]) -> str:
        """
        生成Wiki索引
        
        Args:
            wiki_pages: Wiki页面列表
            
        Returns:
            str: 索引文件路径
        """
        index_content = f"""# Wiki知识库索引

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 快速导航

- [概念 (Concepts)](concepts/) - 核心概念和定义
- [详细信息 (Details)](details/) - 详细内容和说明
- [总结 (Summaries)](summaries/) - 摘要和概述

---

## 所有页面

"""
        
        # 按分类组织
        by_category = {}
        for page in wiki_pages:
            category = page.get('category', 'details')
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(page)
        
        # 输出每个分类的页面
        for category in ['concepts', 'details', 'summaries']:
            if category in by_category:
                index_content += f"\n### {category.capitalize()}\n\n"
                for page in by_category[category]:
                    rel_path = os.path.relpath(page['file_path'], self.output_dir)
                    index_content += f"- [{page['title']}]({rel_path})\n"
        
        # 保存索引文件
        index_file = os.path.join(self.output_dir, 'index.md')
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(index_content)
        
        return index_file
    
    def _generate_navigation(self, wiki_pages: List[Dict[str, Any]]) -> str:
        """
        生成导航文件
        
        Args:
            wiki_pages: Wiki页面列表
            
        Returns:
            str: 导航文件路径
        """
        nav_content = "# 导航\n\n"
        nav_content += "- [首页](index.md)\n"
        nav_content += "\n## 页面列表\n\n"
        
        for i, page in enumerate(wiki_pages, 1):
            rel_path = os.path.relpath(page['file_path'], self.output_dir)
            nav_content += f"{i}. [{page['title']}]({rel_path})\n"
        
        # 保存导航文件
        nav_file = os.path.join(self.output_dir, 'navigation.md')
        with open(nav_file, 'w', encoding='utf-8') as f:
            f.write(nav_content)
        
        return nav_file
