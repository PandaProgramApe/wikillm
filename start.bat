@echo off
chcp 65001 >nul
echo ==================================================
echo   WikiLLM - 基于LLM的知识库编译系统
echo ==================================================
echo.

cd /d "%~dp0"

REM 检查Python是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 检查依赖是否已安装
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [安装] 正在安装依赖...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
    echo [完成] 依赖安装成功
    echo.
)

REM 检查.env配置
if not exist .env (
    if exist .env.example (
        echo [提示] 未找到.env配置文件，已从.env.example复制
        copy .env.example .env >nul
        echo [重要] 请编辑.env文件，填入你的API密钥！
        echo.
    )
)

echo [启动] 正在启动WikiLLM Web服务...
echo [访问] http://localhost:5000
echo.
echo 按 Ctrl+C 停止服务
echo.

python main.py web
pause
