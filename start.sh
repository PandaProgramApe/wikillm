#!/bin/bash
# WikiLLM 启动脚本

echo "=================================================="
echo "  WikiLLM - 基于LLM的知识库编译系统"
echo "=================================================="
echo ""

cd "$(dirname "$0")"

# 检查Python
if ! command -v python &> /dev/null; then
    echo "[错误] 未找到Python，请先安装Python 3.8+"
    exit 1
fi

# 检查依赖
if ! python -c "import flask" &> /dev/null; then
    echo "[安装] 正在安装依赖..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "[错误] 依赖安装失败"
        exit 1
    fi
    echo "[完成] 依赖安装成功"
    echo ""
fi

# 检查.env配置
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo "[提示] 未找到.env配置文件，已从.env.example复制"
        cp .env.example .env
        echo "[重要] 请编辑.env文件，填入你的API密钥！"
        echo ""
    fi
fi

echo "[启动] 正在启动WikiLLM Web服务..."
echo "[访问] http://localhost:5000"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

python main.py web
