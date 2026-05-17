"""
查询引擎
负责在Wiki知识库中搜索和查询信息
"""

import os
import re
from typing import List, Dict, Any, Optional


class QueryEngine:
    """Wiki知识库查询引擎"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化查询引擎
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.wiki_dir = config.get('wiki', {}).get('output_dir', 'data/wiki')
        self.wiki_files = self._load_wiki_files()
    
    def _load_wiki_files(self) -> List[str]:
        """
        加载所有Wiki文件
        
        Returns:
            List[str]: Wiki文件路径列表
        """
        wiki_files = []
        
        if not os.path.exists(self.wiki_dir):
            return wiki_files
        
        # 递归查找所有.md文件
        for root, dirs, files in os.walk(self.wiki_dir):
            for file in files:
                if file.endswith('.md'):
                    wiki_files.append(os.path.join(root, file))
        
        return wiki_files
    
    def reload(self):
        """重新加载Wiki文件"""
        self.wiki_files = self._load_wiki_files()
        print(f"已重新加载 {len(self.wiki_files)} 个Wiki文件")
    
    def keyword_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        关键词搜索
        
        Args:
            query: 搜索关键词
            top_k: 返回前k个结果
            
        Returns:
            List[Dict[str, Any]]: 搜索结果
        """
        if not self.wiki_files:
            return []
        
        results = []
        query_lower = query.lower()
        query_terms = set(re.findall(r'\w+', query_lower))
        
        for wiki_file in self.wiki_files:
            try:
                with open(wiki_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 计算相关性得分
                content_lower = content.lower()
                
                # 1. 精确匹配得分
                exact_matches = content_lower.count(query_lower)
                
                # 2. 术语匹配得分
                term_matches = sum(1 for term in query_terms if term in content_lower)
                
                # 3. 标题匹配加分
                title_bonus = 0
                title_match = re.search(r'^#{1,3}\s+(.+)$', content, re.MULTILINE)
                if title_match:
                    title = title_match.group(1).lower()
                    if query_lower in title:
                        title_bonus = 10
                
                # 总分
                score = exact_matches * 3 + term_matches + title_bonus
                
                if score > 0:
                    # 提取摘要
                    snippet = self._extract_snippet(content, query)
                    
                    results.append({
                        'file': wiki_file,
                        'title': title_match.group(1) if title_match else os.path.basename(wiki_file),
                        'score': score,
                        'snippet': snippet,
                        'content': content,
                    })
            
            except Exception as e:
                print(f"读取文件失败 {wiki_file}: {str(e)}")
                continue
        
        # 按得分排序
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results[:top_k]
    
    def semantic_query(self, question: str, processor, top_k: int = 3) -> str:
        """
        语义查询（使用LLM）
        
        Args:
            question: 用户问题
            processor: LLM处理器
            top_k: 检索的文档数
            
        Returns:
            str: LLM生成的回答
        """
        # 1. 先使用关键词搜索检索相关文档
        relevant_docs = self.keyword_search(question, top_k=top_k)
        
        if not relevant_docs:
            return "抱歉，知识库中没有找到相关信息。"
        
        # 2. 合并相关文档内容
        context = "\n\n---\n\n".join([doc['content'] for doc in relevant_docs])
        
        # 3. 使用LLM基于上下文回答问题
        answer = processor.query(question, context)
        
        # 4. 添加引用信息
        sources = "\n".join([f"- {doc['title']}" for doc in relevant_docs])
        answer += f"\n\n**参考来源：**\n{sources}"
        
        return answer
    
    def hybrid_query(self, question: str, processor, top_k: int = 3) -> Dict[str, Any]:
        """
        混合查询：结合关键词搜索和语义查询
        
        Args:
            question: 用户问题
            processor: LLM处理器
            top_k: 检索的文档数
            
        Returns:
            Dict[str, Any]: 查询结果
        """
        # 1. 关键词搜索
        keyword_results = self.keyword_search(question, top_k=top_k)
        
        # 2. 语义查询
        answer = self.semantic_query(question, processor, top_k=top_k)
        
        return {
            'question': question,
            'answer': answer,
            'keyword_results': keyword_results,
            'total_docs_searched': len(self.wiki_files),
            'relevant_docs': len(keyword_results),
        }
    
    def _extract_snippet(self, content: str, query: str, context_chars: int = 100) -> str:
        """
        提取包含查询词的片段
        
        Args:
            content: 文档内容
            query: 查询词
            context_chars: 上下文字符数
            
        Returns:
            str: 片段
        """
        query_lower = query.lower()
        content_lower = content.lower()
        
        # 查找查询词位置
        pos = content_lower.find(query_lower)
        
        if pos == -1:
            # 如果没找到精确匹配，返回前200个字符
            return content[:200] + '...' if len(content) > 200 else content
        
        # 提取上下文
        start = max(0, pos - context_chars)
        end = min(len(content), pos + len(query) + context_chars)
        
        snippet = content[start:end]
        
        # 添加省略号
        if start > 0:
            snippet = '...' + snippet
        if end < len(content):
            snippet = snippet + '...'
        
        return snippet
    
    def get_all_pages(self) -> List[Dict[str, Any]]:
        """
        获取所有Wiki页面信息
        
        Returns:
            List[Dict[str, Any]]: 页面信息列表
        """
        pages = []
        
        for wiki_file in self.wiki_files:
            try:
                with open(wiki_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 提取标题
                title_match = re.search(r'^#{1,3}\s+(.+)$', content, re.MULTILINE)
                title = title_match.group(1) if title_match else os.path.basename(wiki_file)
                
                # 提取元数据
                metadata = {}
                metadata_match = re.search(r'^---\n(.+?)\n---', content, re.DOTALL | re.MULTILINE)
                if metadata_match:
                    for line in metadata_match.group(1).split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            metadata[key.strip()] = value.strip()
                
                pages.append({
                    'file': wiki_file,
                    'title': title,
                    'metadata': metadata,
                    'characters': len(content),
                    'url': f"/view?file={os.path.basename(wiki_file)}",
                })
            
            except Exception as e:
                print(f"读取文件失败 {wiki_file}: {str(e)}")
                continue
        
        return pages
