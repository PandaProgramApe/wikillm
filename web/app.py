"""
Flask Web应用
提供WikiLLM的Web界面
"""

import os
from flask import Flask, render_template, request, jsonify, send_file
from pathlib import Path


def create_app(config: dict):
    """
    创建Flask应用
    
    Args:
        config: 配置字典
        
    Returns:
        Flask: Flask应用实例
    """
    app = Flask(__name__, 
                template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
                static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    
    # 配置
    app.config['SECRET_KEY'] = 'wikillm-secret-key'
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
    
    # 初始化处理器和引擎
    from processors import ProcessorFactory
    from core import DocumentProcessor, WikiBuilder, QueryEngine
    
    processor = None
    doc_processor = DocumentProcessor(config)
    wiki_builder = WikiBuilder(config)
    query_engine = QueryEngine(config)
    
    # 路由
    @app.route('/')
    def index():
        """首页"""
        return render_template('index.html')
    
    @app.route('/upload', methods=['POST'])
    def upload_file():
        """上传文档"""
        nonlocal processor
        
        if 'file' not in request.files:
            return jsonify({'error': '没有上传文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '未选择文件'}), 400
        
        # 保存文件
        from werkzeug.utils import secure_filename
        filename = secure_filename(file.filename)
        upload_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # 处理文档
        if processor is None:
            try:
                processor = ProcessorFactory.create(config=config)
            except Exception as e:
                return jsonify({'error': f'LLM处理器初始化失败: {str(e)}'}), 500
        
        try:
            result = doc_processor.process_document(file_path, processor)
            return jsonify({
                'success': True,
                'result': {
                    'source_file': result['source_file'],
                    'output_file': os.path.basename(result['output_file']),
                    'chunks_count': result['chunks_count'],
                    'total_characters': result['total_characters'],
                    'wiki_characters': result['wiki_characters'],
                }
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/query', methods=['POST'])
    def query():
        """查询知识库"""
        nonlocal processor
        
        data = request.get_json()
        question = data.get('question', '')
        
        if not question:
            return jsonify({'error': '问题不能为空'}), 400
        
        if processor is None:
            try:
                processor = ProcessorFactory.create(config=config)
            except Exception as e:
                return jsonify({'error': f'LLM处理器初始化失败: {str(e)}'}), 500
        
        try:
            result = query_engine.hybrid_query(question, processor)
            return jsonify({
                'success': True,
                'result': result
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/pages')
    def list_pages():
        """列出所有Wiki页面"""
        pages = query_engine.get_all_pages()
        return jsonify({'success': True, 'pages': pages})
    
    @app.route('/view/<filename>')
    def view_page(filename):
        """查看Wiki页面"""
        import markdown as md
        wiki_dir = config.get('wiki', {}).get('output_dir', 'data/wiki')
        file_path = os.path.join(wiki_dir, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': '文件不存在'}), 404
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 将Markdown转换为HTML
        html_content = md.markdown(
            content,
            extensions=['tables', 'fenced_code', 'toc', 'nl2br']
        )
        
        return render_template('view.html', content=html_content, filename=filename)
    
    @app.route('/api/reload')
    def reload():
        """重新加载知识库"""
        query_engine.reload()
        return jsonify({'success': True, 'message': '知识库已重新加载'})
    
    return app
