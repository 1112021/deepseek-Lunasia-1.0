# -*- coding: utf-8 -*-
"""
露尼西亚AI助手 - 主程序入口
重构后的模块化版本
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtCore import Qt

# 导入自定义模块
from config import load_config
from ai_agent import AIAgent
from main_window import AIAgentApp

def main():
    """主程序入口"""
    # 创建Qt应用程序
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle("Fusion")
    
    # 创建调色板
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(30, 30, 46))  # 深蓝色背景
    palette.setColor(QPalette.WindowText, QColor(205, 214, 244))  # 浅蓝色文本
    palette.setColor(QPalette.Base, QColor(24, 24, 37))  # 更深的基础色
    palette.setColor(QPalette.AlternateBase, QColor(49, 50, 68))  # 交替基础色
    palette.setColor(QPalette.ToolTipBase, QColor(180, 190, 254))  # 工具提示基础色
    palette.setColor(QPalette.ToolTipText, QColor(24, 24, 37))  # 工具提示文本
    palette.setColor(QPalette.Text, QColor(205, 214, 244))  # 文本颜色
    palette.setColor(QPalette.Button, QColor(49, 50, 68))  # 按钮颜色
    palette.setColor(QPalette.ButtonText, QColor(205, 214, 244))  # 按钮文本
    palette.setColor(QPalette.BrightText, QColor(245, 224, 220))  # 亮色文本
    palette.setColor(QPalette.Highlight, QColor(137, 180, 250))  # 高亮色
    palette.setColor(QPalette.HighlightedText, QColor(24, 24, 37))  # 高亮文本
    
    app.setPalette(palette)
    
    # 设置字体
    font = QFont("Microsoft YaHei UI", 10)
    app.setFont(font)
    
    # 加载配置
    config = load_config()
    
    # 创建主窗口
    window = AIAgentApp(config)
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

