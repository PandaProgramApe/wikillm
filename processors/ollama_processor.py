"""
Ollama处理器
支持本地运行的Ollama模型
"""

import json
import requests
from typing import List, Dict, Any
from .base_processor import BaseProcessor


class OllamaProcessor(BaseProcessor):
    """Ollama本地模型处理器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化Ollama处理器

        Args:
            config: 配置字典，包含base_url, model等
        """
        super().__init__(config)

        self.base_url = config.get('base_url', 'http://localhost:11434').rstrip('/')
        self.model = config.get('model', 'llama3.2')

        # 自动探测可用API端点（优先 /api/chat，回退 /api/generate）
        self._api_endpoint = self._detect_endpoint()

        # 验证Ollama服务是否可用
        self._check_ollama_service()

    def _detect_endpoint(self) -> str:
        """
        自动探测Ollama可用的API端点。
        新版Ollama使用 /api/chat，旧版使用 /api/generate。

        Returns:
            str: 可用的端点名称 ('chat' 或 'generate')
        """
        try:
            resp = requests.post(
                f"{self.base_url}/api/chat",
                json={"model": self.model, "messages": [{"role": "user", "content": "hi"}], "stream": False},
                timeout=10,
            )
            if resp.status_code == 200:
                print("[Ollama] 检测到 /api/chat 端点可用（新版）")
                return "chat"
        except Exception:
            pass

        try:
            resp = requests.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": "hi", "stream": False},
                timeout=10,
            )
            if resp.status_code == 200:
                print("[Ollama] 检测到 /api/generate 端点可用（旧版）")
                return "generate"
        except Exception:
            pass

        # 默认使用 /api/chat，让后续调用自然报错以提供更好的错误提示
        return "chat"

    def _check_ollama_service(self):
        """检查Ollama服务是否运行"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                raise ConnectionError(
                    f"Ollama服务不可用。请确保Ollama正在运行在 {self.base_url}"
                )
        except requests.exceptions.RequestException as e:
            raise ConnectionError(
                f"无法连接到Ollama服务 ({self.base_url})。"
                "请确保Ollama已安装并正在运行。"
                "安装说明: https://ollama.com"
            )

    def _call_api(self, prompt: str, system: str = None, **kwargs) -> str:
        """
        调用Ollama API，自动根据检测到的端点选择请求方式。

        Args:
            prompt: 用户提示词
            system: 系统提示词（可选）
            **kwargs: 其他参数

        Returns:
            str: 模型响应内容
        """
        options = {
            "temperature": kwargs.get('temperature', self.temperature),
            "num_predict": kwargs.get('max_tokens', self.max_tokens),
        }

        if self._api_endpoint == "chat":
            return self._call_chat_api(prompt, system, options)
        else:
            return self._call_generate_api(prompt, system, options)

    def _call_chat_api(self, prompt: str, system: str, options: dict) -> str:
        """
        使用 /api/chat 端点（新版Ollama推荐）

        Args:
            prompt: 用户提示词
            system: 系统提示词
            options: 生成参数

        Returns:
            str: 模型响应内容
        """
        url = f"{self.base_url}/api/chat"

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": options,
        }

        try:
            response = requests.post(url, json=payload, timeout=180)
            response.raise_for_status()
            result = response.json()
            return result.get('message', {}).get('content', '')
        except requests.exceptions.Timeout:
            raise TimeoutError(
                "Ollama API调用超时。这可能是因为模型太大或系统资源不足。"
                "请尝试使用更小的模型或增加超时时间。"
            )
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(
                f"Ollama API调用失败 (HTTP {e.response.status_code})。"
                f"请确认模型 '{self.model}' 已拉取: ollama pull {self.model}"
            )
        except Exception as e:
            raise RuntimeError(f"Ollama API调用失败: {str(e)}")

    def _call_generate_api(self, prompt: str, system: str, options: dict) -> str:
        """
        使用 /api/generate 端点（旧版Ollama兼容）

        Args:
            prompt: 用户提示词
            system: 系统提示词
            options: 生成参数

        Returns:
            str: 模型响应内容
        """
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": options,
        }

        if system:
            payload["system"] = system

        try:
            response = requests.post(url, json=payload, timeout=180)
            response.raise_for_status()
            result = response.json()
            return result.get('response', '')
        except requests.exceptions.Timeout:
            raise TimeoutError(
                "Ollama API调用超时。这可能是因为模型太大或系统资源不足。"
                "请尝试使用更小的模型或增加超时时间。"
            )
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(
                f"Ollama API调用失败 (HTTP {e.response.status_code})。"
                f"请确认模型 '{self.model}' 已拉取: ollama pull {self.model}"
            )
        except Exception as e:
            raise RuntimeError(f"Ollama API调用失败: {str(e)}")
    
    def analyze(self, content: str) -> str:
        """
        分析文档内容，提取关键信息
        
        Args:
            content: 文档内容
            
        Returns:
            str: 分析结果
        """
        prompt = self.config.get('prompts', {}).get('analyze', '')
        if not prompt:
            prompt = """
你是一个知识整理专家。请分析以下文档内容，提取关键信息：
1. 核心概念和定义
2. 主要论点和结论
3. 重要细节和示例
4. 章节结构和逻辑关系

文档内容：
{content}

请以结构化的方式输出分析结果。
"""
        
        prompt = prompt.replace('{content}', content)
        
        return self._call_api(
            prompt=prompt,
            system="你是一个专业的知识整理和分析专家。"
        )
    
    def compile(self, analysis: str) -> str:
        """
        将分析结果编译成Wiki文章
        
        Args:
            analysis: 分析结果
            
        Returns:
            str: 编译后的Wiki文章（Markdown格式）
        """
        prompt = self.config.get('prompts', {}).get('compile', '')
        if not prompt:
            prompt = """
你是一个Wiki编写专家。基于以下分析结果，编写一篇结构清晰、易于理解的Wiki文章：

分析结果：
{analysis}

要求：
1. 使用Markdown格式
2. 结构清晰，包含标题、子标题
3. 重要概念加粗
4. 添加适当的链接和引用
5. 语言简洁明了

请直接输出Wiki文章内容。
"""
        
        prompt = prompt.replace('{analysis}', analysis)
        
        return self._call_api(
            prompt=prompt,
            system="你是一个专业的Wiki编写专家。"
        )
    
    def query(self, question: str, context: str) -> str:
        """
        基于Wiki知识库回答问题
        
        Args:
            question: 用户问题
            context: 相关上下文/Wiki内容
            
        Returns:
            str: 回答
        """
        prompt = f"""
基于以下Wiki知识库内容，回答用户的问题。如果知识库中没有相关信息，请明确说明。

Wiki知识库内容：
{context}

用户问题：{question}

请提供准确、详细的回答，并引用知识库中的相关内容。
"""
        
        return self._call_api(
            prompt=prompt,
            system="你是一个知识库问答专家，基于提供的知识库内容回答用户问题。"
        )
    
    def summarize(self, content: str, max_length: int = 500) -> str:
        """
        总结内容
        
        Args:
            content: 要总结的内容
            max_length: 最大长度（字符数）
            
        Returns:
            str: 总结
        """
        # 如果内容本身就很短，直接返回
        if len(content) <= max_length:
            return content
        
        prompt = f"""
请对以下内容进行总结，总结长度控制在{max_length}字符以内。
保持关键信息和核心观点。

内容：
{content}

请直接输出总结，不要添加额外的解释。
"""
        
        summary = self._call_api(
            prompt=prompt,
            system="你是一个文本总结专家。"
        )
        
        # 如果总结还是太长，截断
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."
        
        return summary
    
    def list_models(self) -> List[str]:
        """
        列出可用的Ollama模型
        
        Returns:
            List[str]: 模型名称列表
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            result = response.json()
            models = [model['name'] for model in result.get('models', [])]
            return models
        except Exception as e:
            raise RuntimeError(f"获取Ollama模型列表失败: {str(e)}")
