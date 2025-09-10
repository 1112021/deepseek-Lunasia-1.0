@echo off
chcp 65001 >nul
title 露尼西亚AI助手

echo.
echo ========================================
echo           露尼西亚AI助手
echo ========================================
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未找到Python，请先安装Python 3.8或更高版本
    echo.
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 显示Python版本
echo ✅ Python版本：
python --version

:: 检查是否在项目目录
if not exist "main.py" (
    echo ❌ 错误：未找到main.py文件
    echo 请确保在露尼西亚项目目录中运行此脚本
    pause
    exit /b 1
)

:: 检查依赖是否安装
echo.
echo 🔍 检查依赖包...
python -c "import PyQt5" >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未找到PyQt5，正在安装依赖包...
    echo.
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ 依赖安装失败，请手动运行：pip install -r requirements.txt
        pause
        exit /b 1
    )
    echo ✅ 依赖安装完成
)

echo ✅ 依赖检查完成
echo.

:: 启动露尼西亚
echo 🚀 正在启动露尼西亚AI助手...
echo.
python main.py

:: 如果程序异常退出，显示错误信息
if errorlevel 1 (
    echo.
    echo ❌ 程序异常退出，错误代码：%errorlevel%
    echo.
    echo 可能的解决方案：
    echo 1. 检查配置文件是否正确
    echo 2. 确保所有依赖包已安装
    echo 3. 检查API密钥配置
    echo.
)

echo.
echo 按任意键退出...
pause >nul
