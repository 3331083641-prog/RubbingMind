@echo off
chcp 65001 >nul
title 墨韵智考 一键启动服务

echo ======================================================================
echo    墨韵智考——金石碑拓微痕修复及智能史料考据系统
echo    全球校园人工智能算法精英大赛（智能文化赛道）参赛项目
echo ======================================================================
echo.

cd /d "%~dp0"

echo [1/3] 正在检测 Python 环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python 环境，请确认已安装 Python 3.10+ 并加入系统环境变量 PATH！
    pause
    exit /b 1
)

echo [2/3] 正在检查依赖项...
python -c "import cv2, numpy, skimage, fastapi, uvicorn" >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在安装必要依赖...
    pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com --quiet
)

echo [3/3] 正在启动服务并打开浏览器大屏...
start "" cmd /c "timeout /t 2 >nul & start http://127.0.0.1:8000"

echo.
echo ======================================================================
echo 服务正在 http://127.0.0.1:8000 运行中...
echo 如需停止服务，请按 Ctrl + C 关闭此窗口。
echo ======================================================================
echo.

python main.py
pause
