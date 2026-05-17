"""
WikiLLM - 基于LLM的知识库编译系统
主程序入口

使用方法:
    python main.py              # 启动Web服务
    python main.py --help       # 查看帮助
    python main.py compile FILE # 编译单个文档
    python main.py query "问题" # 查询知识库
"""

import os
import sys
import argparse
import yaml
from pathlib import Path

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)


def load_config(config_path: str = None) -> dict:
    """
    加载配置文件
    
    Args:
        config_path: 配置文件路径（可选）
        
    Returns:
        dict: 配置字典
    """
    if config_path is None:
        config_path = os.path.join(project_root, 'config', 'config.yaml')
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 加载.env文件
    try:
        from dotenv import load_dotenv
        env_path = os.path.join(project_root, '.env')
        if os.path.exists(env_path):
            load_dotenv(env_path)
    except ImportError:
        print("提示: 安装python-dotenv可以支持.env配置文件")
    
    # 替换环境变量
    import re
    def replace_env(match):
        var_name = match.group(1)
        return os.getenv(var_name, match.group(0))
    
    config_str = yaml.dump(config)
    config_str = re.sub(r'\$\{(\w+)\}', replace_env, config_str)
    config = yaml.safe_load(config_str)
    
    return config


def cmd_compile(args, config: dict):
    """编译文档命令"""
    from processors import ProcessorFactory
    from core import DocumentProcessor

    print(f"正在编译文档: {args.file}")

    # 流式输出：CLI默认开启，Web模式下关闭
    config.setdefault('llm', {})
    if args.stream:
        config['llm']['stream'] = True

    # 创建处理器
    processor = ProcessorFactory.create(provider=args.provider, config=config)
    print(f"使用LLM: {processor.get_provider_name()} ({processor.model})")

    # 处理文档
    doc_processor = DocumentProcessor(config)
    result = doc_processor.process_document(args.file, processor, save=not args.dry_run)

    if args.dry_run:
        print("\n--- Wiki内容预览 ---")
        print(result['wiki_content'][:1000])
        if len(result['wiki_content']) > 1000:
            print(f"\n... (共 {len(result['wiki_content'])} 字符)")

    print(f"\n编译完成！")
    print(f"  源文件: {result['source_file']}")
    print(f"  输出文件: {result['output_file']}")
    print(f"  分块数: {result['chunks_count']}")
    print(f"  Wiki长度: {result['wiki_characters']} 字符")
    if 'total_time' in result:
        print(f"  总耗时: {result['total_time']}s")


def cmd_query(args, config: dict):
    """查询命令"""
    from processors import ProcessorFactory
    from core import QueryEngine
    
    # 创建处理器
    processor = ProcessorFactory.create(provider=args.provider, config=config)
    query_engine = QueryEngine(config)
    
    # 执行查询
    result = query_engine.hybrid_query(args.question, processor)
    
    print(f"\n问题: {result['question']}")
    print(f"相关文档: {result['relevant_docs']}/{result['total_docs_searched']}")
    print(f"\n--- 回答 ---")
    print(result['answer'])


def cmd_build(args, config: dict):
    """构建知识库命令"""
    from processors import ProcessorFactory
    from core import DocumentProcessor, WikiBuilder
    import glob
    
    # 查找所有原始文档
    raw_dir = os.path.join(project_root, 'data', 'raw')
    supported_exts = config.get('document', {}).get('supported_formats', 
                                                     ['.pdf', '.docx', '.doc', '.md', '.txt'])
    
    files = []
    for ext in supported_exts:
        files.extend(glob.glob(os.path.join(raw_dir, '*' + ext)))
    
    if not files:
        print(f"在 {raw_dir} 中未找到文档。")
        print(f"支持的格式: {', '.join(supported_exts)}")
        return
    
    print(f"找到 {len(files)} 个文档需要处理")
    
    # 创建处理器
    processor = ProcessorFactory.create(provider=args.provider, config=config)
    doc_processor = DocumentProcessor(config)
    
    # 批量处理
    results = doc_processor.batch_process(files, processor)
    
    # 构建Wiki
    wiki_builder = WikiBuilder(config)
    wiki_result = wiki_builder.build_wiki(results)
    
    print(f"\n知识库构建完成！")
    print(f"  总页面数: {wiki_result['total_pages']}")
    print(f"  索引文件: {wiki_result['index_file']}")
    print(f"  输出目录: {wiki_result['output_dir']}")


def cmd_web(args, config: dict):
    """启动Web服务"""
    from web import create_app
    
    host = config.get('web', {}).get('host', '0.0.0.0')
    port = args.port or config.get('web', {}).get('port', 5000)
    debug = config.get('web', {}).get('debug', False)
    
    app = create_app(config)
    
    print(f"\n{'='*50}")
    print(f"  WikiLLM Web服务已启动")
    print(f"  访问地址: http://localhost:{port}")
    print(f"{'='*50}\n")
    
    app.run(host=host, port=port, debug=debug)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='WikiLLM - 基于LLM的知识库编译系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py                      启动Web服务
  python main.py compile doc.pdf      编译PDF文档
  python main.py query "什么是AI"     查询知识库
  python main.py build                构建知识库
  python main.py compile -p ollama    使用Ollama本地模型
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # web命令（默认）
    web_parser = subparsers.add_parser('web', help='启动Web服务')
    web_parser.add_argument('--port', '-p', type=int, help='端口号')
    web_parser.add_argument('--config', '-c', help='配置文件路径')
    
    # compile命令
    compile_parser = subparsers.add_parser('compile', help='编译文档')
    compile_parser.add_argument('file', help='文档路径')
    compile_parser.add_argument('--provider', '-p', choices=['openai', 'ollama', 'deepseek'],
                                help='LLM提供商')
    compile_parser.add_argument('--dry-run', '-n', action='store_true',
                                help='只预览不保存')
    compile_parser.add_argument('--stream', '-s', action='store_true',
                                help='流式输出（实时显示生成内容）')
    compile_parser.add_argument('--config', '-c', help='配置文件路径')
    
    # query命令
    query_parser = subparsers.add_parser('query', help='查询知识库')
    query_parser.add_argument('question', help='查询问题')
    query_parser.add_argument('--provider', '-p', choices=['openai', 'ollama', 'deepseek'],
                              help='LLM提供商')
    query_parser.add_argument('--config', '-c', help='配置文件路径')
    
    # build命令
    build_parser = subparsers.add_parser('build', help='构建知识库')
    build_parser.add_argument('--provider', '-p', choices=['openai', 'ollama', 'deepseek'],
                              help='LLM提供商')
    build_parser.add_argument('--config', '-c', help='配置文件路径')
    
    args = parser.parse_args()
    
    # 加载配置
    config_path = getattr(args, 'config', None)
    try:
        config = load_config(config_path)
    except FileNotFoundError as e:
        print(f"错误: {e}")
        print("请确保config/config.yaml文件存在")
        sys.exit(1)
    
    # 执行命令
    if args.command == 'compile':
        cmd_compile(args, config)
    elif args.command == 'query':
        cmd_query(args, config)
    elif args.command == 'build':
        cmd_build(args, config)
    else:
        # 默认启动Web服务
        args.command = 'web'
        args.port = None
        cmd_web(args, config)


if __name__ == '__main__':
    main()
