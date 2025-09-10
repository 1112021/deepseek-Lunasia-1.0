@echo off
chcp 65001 >nul
title 露尼西亚AI助手 - 快速启动

echo 🚀 启动露尼西亚AI助手...
python main.py

if errorlevel 1 (
    echo.
    echo ❌ 启动失败，请检查Python环境和依赖包
    pause
)
