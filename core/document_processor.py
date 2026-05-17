"""
文档处理器
整合文档加载器和LLM处理器，实现完整的文档处理流程
"""

import os
import hashlib
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


class DocumentProcessor:
    """文档处理器，协调文档加载和LLM处理"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化文档处理器

        Args:
            config: 配置字典
        """
        self.config = config
        self.output_dir = config.get('wiki', {}).get('output_dir', 'data/wiki')
        # 并发数：默认 5，可通过 config.document.max_workers 配置
        self.max_workers = config.get('document', {}).get('max_workers', 5)
        os.makedirs(self.output_dir, exist_ok=True)

    def process_document(self, file_path: str, processor, save: bool = True) -> Dict[str, Any]:
        """
        处理单个文档：加载 → 分析 → 编译 → 保存

        Args:
            file_path: 文档路径
            processor: LLM处理器实例
            save: 是否保存结果到文件

        Returns:
            Dict[str, Any]: 处理结果
        """
        from loaders import get_loader

        total_start = time.time()

        # 1. 加载文档
        print(f"正在加载文档: {file_path}")
        loader = get_loader(file_path)
        content = loader.load()

        if not content or not content.strip():
            raise ValueError(f"文档内容为空: {file_path}")

        print(f"文档加载成功，共 {len(content)} 字符")

        # 2. 分块处理（如果文档太长）
        chunk_size = self.config.get('document', {}).get('chunk_size', 2000)
        chunks = processor.chunk_text(content, chunk_size=chunk_size)

        print(f"文档分为 {len(chunks)} 个块进行处理")
        print(f"使用 {self.max_workers} 个并发线程分析...")

        # 3. 并行分析每个块
        analyses = self._parallel_analyze(chunks, processor)

        # 4. 合并分析结果
        combined_analysis = "\n\n---\n\n".join(analyses)

        # 5. 编译成Wiki文章
        print("正在编译Wiki文章...")
        compile_start = time.time()
        wiki_content = processor.compile(combined_analysis)
        compile_time = time.time() - compile_start
        print(f"  编译完成 ({compile_time:.1f}s)")

        # 6. 生成输出文件路径
        file_name = os.path.splitext(os.path.basename(file_path))[0]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(self.output_dir, f"{file_name}_{timestamp}.md")

        total_time = time.time() - total_start

        # 7. 保存结果
        result = {
            'source_file': file_path,
            'output_file': output_file,
            'wiki_content': wiki_content,
            'analysis': combined_analysis,
            'chunks_count': len(chunks),
            'total_characters': len(content),
            'wiki_characters': len(wiki_content),
            'processed_at': datetime.now().isoformat(),
            'total_time': round(total_time, 2),
        }

        if save:
            print(f"正在保存Wiki文章到: {output_file}")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(wiki_content)
            result['saved'] = True
        else:
            result['saved'] = False

        print(f"文档处理完成！总耗时 {total_time:.1f}s")
        return result

    def _parallel_analyze(self, chunks: List[str], processor) -> List[str]:
        """
        并行分析多个文档块

        Args:
            chunks: 文档块列表
            processor: LLM处理器实例

        Returns:
            List[str]: 分析结果列表（保持原始顺序）
        """
        total = len(chunks)

        # 如果只有 1 块或并发数为 1，直接串行处理
        if total <= 1 or self.max_workers <= 1:
            return [processor.analyze(chunk) for chunk in chunks]

        results = [None] * total
        completed = 0
        start = time.time()

        def _analyze_chunk(index: int, chunk: str) -> tuple:
            """分析单个块，返回 (index, result)"""
            return index, processor.analyze(chunk)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(_analyze_chunk, i, chunk): i
                for i, chunk in enumerate(chunks)
            }

            for future in as_completed(futures):
                idx, analysis = future.result()
                results[idx] = analysis
                completed += 1
                elapsed = time.time() - start
                speed = completed / elapsed if elapsed > 0 else 0
                eta = (total - completed) / speed if speed > 0 else 0
                print(f"  分析块 {completed}/{total} 完成 "
                      f"({elapsed:.1f}s, 预计剩余 {eta:.0f}s)")

        elapsed = time.time() - start
        print(f"  全部分析完成，耗时 {elapsed:.1f}s "
              f"(平均 {elapsed/total:.1f}s/块)")
        return results

    def batch_process(self, file_paths: List[str], processor, save: bool = True) -> List[Dict[str, Any]]:
        """
        批量处理多个文档

        Args:
            file_paths: 文档路径列表
            processor: LLM处理器实例
            save: 是否保存结果

        Returns:
            List[Dict[str, Any]]: 处理结果列表
        """
        results = []

        for i, file_path in enumerate(file_paths):
            print(f"\n处理文档 {i+1}/{len(file_paths)}: {file_path}")
            try:
                result = self.process_document(file_path, processor, save)
                results.append(result)
            except Exception as e:
                print(f"处理文档失败: {str(e)}")
                results.append({
                    'source_file': file_path,
                    'error': str(e),
                    'processed_at': datetime.now().isoformat(),
                })

        return results
    
    def generate_index(self, wiki_files: List[str], output_file: str = None) -> str:
        """
        生成Wiki索引文件
        
        Args:
            wiki_files: Wiki文件路径列表
            output_file: 输出文件路径（可选）
            
        Returns:
            str: 索引内容
        """
        index_content = "# Wiki知识库索引\n\n"
        index_content += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        index_content += "## 文档列表\n\n"
        
        for i, wiki_file in enumerate(wiki_files, 1):
            file_name = os.path.basename(wiki_file)
            index_content += f"{i}. [{file_name}]({wiki_file})\n"
        
        index_content += "\n---\n\n"
        index_content += "## 使用说明\n\n"
        index_content += "1. 点击上方链接查看各个Wiki文档\n"
        index_content += "2. 使用查询功能搜索知识库内容\n"
        index_content += "3. Wiki文档会持续更新和积累\n"
        
        # 保存索引文件
        if output_file is None:
            output_file = os.path.join(self.output_dir, 'index.md')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(index_content)
        
        print(f"索引文件已生成: {output_file}")
        return index_content
