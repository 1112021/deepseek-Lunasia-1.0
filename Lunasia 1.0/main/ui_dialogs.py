# -*- coding: utf-8 -*-
"""
UI对话框模块
包含设置、记忆系统、MCP工具等对话框
"""

import os
import json
import datetime
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit,
                             QPushButton, QLabel, QComboBox, QSplitter, QListWidget,
                             QGroupBox, QFormLayout, QMessageBox, QInputDialog, 
                             QFileDialog, QProgressBar, QListWidgetItem, QTabWidget,
                             QSlider, QCheckBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon

from config import save_config
from utils import scan_windows_apps
from memory_lake import MemoryLake
from mcp_server import LocalMCPServer

class SettingsDialog(QDialog):
    """设置对话框"""
    
    def __init__(self, config, parent=None, transparency_callback=None):
        super().__init__(parent)
        self.config = config
        self.transparency_callback = transparency_callback  # 透明度更新回调
        self.setWindowTitle("AI助手设置")
        self.setGeometry(300, 300, 600, 1200)  # 设置初始高度为1200px
        
        # 设置窗口大小策略，只允许垂直调整高度，不允许调整宽度
        from PyQt5.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.setMinimumWidth(600)  # 设置最小宽度
        self.setMaximumWidth(600)  # 设置最大宽度，与最小宽度相同，锁定宽度
        self.setMinimumHeight(400)  # 设置最小高度

        # 设置图标
        if os.path.exists("icon.ico"):
            self.setWindowIcon(QIcon("icon.ico"))

        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()

        # API设置
        api_group = QGroupBox("API设置")
        api_layout = QFormLayout()

        self.openai_key_edit = QLineEdit()
        self.openai_key_edit.setText(self.config.get("openai_key", ""))
        self.openai_key_edit.setPlaceholderText("输入OpenAI API密钥")
        api_layout.addRow("OpenAI API密钥:", self.openai_key_edit)

        self.deepseek_key_edit = QLineEdit()
        self.deepseek_key_edit.setText(self.config.get("deepseek_key", ""))
        self.deepseek_key_edit.setPlaceholderText("输入DeepSeek API密钥")
        api_layout.addRow("DeepSeek API密钥:", self.deepseek_key_edit)

        self.weather_key_edit = QLineEdit()
        self.weather_key_edit.setText(self.config.get("heweather_key", ""))
        self.weather_key_edit.setPlaceholderText("输入和风天气API密钥")
        api_layout.addRow("和风天气API密钥:", self.weather_key_edit)

        self.amap_key_edit = QLineEdit()
        self.amap_key_edit.setText(self.config.get("amap_key", ""))
        self.amap_key_edit.setPlaceholderText("输入高德地图API密钥")
        api_layout.addRow("高德地图API密钥:", self.amap_key_edit)

        # 天气数据来源设置
        self.weather_source_combo = QComboBox()
        self.weather_source_combo.addItems(["和风天气API", "高德地图API"])
        current_source = self.config.get("weather_source", "和风天气API")
        index = self.weather_source_combo.findText(current_source)
        if index >= 0:
            self.weather_source_combo.setCurrentIndex(index)
        api_layout.addRow("天气数据来源:", self.weather_source_combo)

        api_group.setLayout(api_layout)

        # 浏览器设置
        browser_group = QGroupBox("浏览器设置")
        browser_layout = QFormLayout()

        self.default_browser_combo = QComboBox()
        self.default_browser_combo.addItems(["默认浏览器", "chrome", "firefox", "edge", "opera", "safari"])
        current_browser = self.config.get("default_browser", "")
        if current_browser:
            index = self.default_browser_combo.findText(current_browser)
            if index >= 0:
                self.default_browser_combo.setCurrentIndex(index)
        browser_layout.addRow("默认浏览器:", self.default_browser_combo)

        self.default_search_engine_combo = QComboBox()
        self.default_search_engine_combo.addItems(["baidu", "google", "bing", "sogou", "360"])
        current_engine = self.config.get("default_search_engine", "baidu")
        index = self.default_search_engine_combo.findText(current_engine)
        if index >= 0:
            self.default_search_engine_combo.setCurrentIndex(index)
        browser_layout.addRow("默认搜索引擎:", self.default_search_engine_combo)

        browser_group.setLayout(browser_layout)

        # 模型选择
        model_group = QGroupBox("模型设置")
        model_layout = QFormLayout()

        self.chat_model_combo = QComboBox()
        self.chat_model_combo.addItems(["deepseek-chat", "deepseek-coder", "deepseek-reasoner", "gpt-4-turbo", "gpt-3.5-turbo"])
        self.chat_model_combo.setCurrentText(self.config.get("selected_model", "deepseek-chat"))
        model_layout.addRow("AI模型:", self.chat_model_combo)

        # 识底深湖模型选择
        self.memory_model_combo = QComboBox()
        self.memory_model_combo.addItems(["deepseek-chat", "deepseek-coder", "deepseek-reasoner", "gpt-4-turbo", "gpt-3.5-turbo"])
        self.memory_model_combo.setCurrentText(self.config.get("memory_summary_model", "deepseek-reasoner"))
        model_layout.addRow("识底深湖模型:", self.memory_model_combo)

        # AI Token数设置
        self.max_tokens_edit = QLineEdit()
        max_tokens = self.config.get("max_tokens", "1000")
        self.max_tokens_edit.setText(str(max_tokens))
        self.max_tokens_edit.setPlaceholderText("输入最大token数，0表示无限制")
        model_layout.addRow("最大Token数:", self.max_tokens_edit)

        model_group.setLayout(model_layout)

        # 界面设置
        ui_group = QGroupBox("界面设置")
        ui_layout = QFormLayout()

        # 窗口透明度设置
        self.transparency_slider = QSlider(Qt.Horizontal)
        self.transparency_slider.setMinimum(30)  # 最小30%透明度
        self.transparency_slider.setMaximum(100)  # 最大100%不透明
        transparency_value = self.config.get("window_transparency", 100)
        self.transparency_slider.setValue(transparency_value)
        self.transparency_slider.setTickPosition(QSlider.TicksBelow)
        self.transparency_slider.setTickInterval(10)
        
        self.transparency_label = QLabel(f"{transparency_value}%")
        self.transparency_slider.valueChanged.connect(self.on_transparency_changed)
        
        transparency_layout = QHBoxLayout()
        transparency_layout.addWidget(self.transparency_slider)
        transparency_layout.addWidget(self.transparency_label)
        ui_layout.addRow("窗口透明度:", transparency_layout)

        # 记忆系统设置
        self.show_remember_details_checkbox = QCheckBox("显示'记住这个时刻'的详细信息")
        show_remember_details = self.config.get("show_remember_details", True)
        self.show_remember_details_checkbox.setChecked(show_remember_details)
        ui_layout.addRow("记忆系统:", self.show_remember_details_checkbox)

        # AI智能创建后备机制设置
        self.ai_fallback_checkbox = QCheckBox("启用AI智能创建的后备机制（关键词识别）")
        ai_fallback_enabled = self.config.get("ai_fallback_enabled", True)
        self.ai_fallback_checkbox.setChecked(ai_fallback_enabled)
        ui_layout.addRow("AI创建:", self.ai_fallback_checkbox)

        # AI智能总结后备方案设置
        self.ai_summary_checkbox = QCheckBox("启用AI智能总结后备方案（关键词识别）")
        ai_summary_enabled = self.config.get("ai_summary_enabled", True)
        self.ai_summary_checkbox.setChecked(ai_summary_enabled)
        ui_layout.addRow("AI总结后备:", self.ai_summary_checkbox)

        # 默认保存路径设置
        default_save_path_layout = QHBoxLayout()
        self.default_save_path_edit = QLineEdit()
        self.default_save_path_edit.setText(self.config.get("default_save_path", "D:/露尼西亚文件/"))
        self.default_save_path_edit.setPlaceholderText("输入默认保存路径")
        self.browse_path_button = QPushButton("浏览...")
        self.browse_path_button.clicked.connect(self.browse_default_save_path)
        default_save_path_layout.addWidget(self.default_save_path_edit)
        default_save_path_layout.addWidget(self.browse_path_button)
        ui_layout.addRow("默认保存路径:", default_save_path_layout)

        # 笔记文件名格式设置
        self.filename_format_combo = QComboBox()
        self.filename_format_combo.addItems(["时间戳格式 (推荐)", "简单格式"])
        filename_format = self.config.get("note_filename_format", "timestamp")
        if filename_format == "simple":
            self.filename_format_combo.setCurrentIndex(1)
        else:
            self.filename_format_combo.setCurrentIndex(0)
        ui_layout.addRow("笔记文件名格式:", self.filename_format_combo)

        ui_group.setLayout(ui_layout)

        # TTS设置
        tts_group = QGroupBox("语音合成 (TTS) 设置")
        tts_layout = QFormLayout()

        # TTS启用开关
        self.tts_enabled_checkbox = QCheckBox("启用语音合成")
        tts_enabled = self.config.get("tts_enabled", False)
        self.tts_enabled_checkbox.setChecked(tts_enabled)
        tts_layout.addRow("TTS功能:", self.tts_enabled_checkbox)

        # Azure TTS API密钥
        self.azure_tts_key_edit = QLineEdit()
        self.azure_tts_key_edit.setText(self.config.get("azure_tts_key", ""))
        self.azure_tts_key_edit.setPlaceholderText("输入Azure Speech Service API密钥")
        self.azure_tts_key_edit.setEchoMode(QLineEdit.Password)
        tts_layout.addRow("Azure TTS API密钥:", self.azure_tts_key_edit)

        # Azure区域
        self.azure_region_combo = QComboBox()
        self.azure_region_combo.addItems([
            "eastasia (东亚)",
            "southeastasia (东南亚)", 
            "eastus (美国东部)",
            "westus (美国西部)",
            "northeurope (北欧)",
            "westeurope (西欧)"
        ])
        current_region = self.config.get("azure_region", "eastasia")
        region_text = f"{current_region} ({self._get_region_name(current_region)})"
        index = self.azure_region_combo.findText(region_text)
        if index >= 0:
            self.azure_region_combo.setCurrentIndex(index)
        tts_layout.addRow("Azure区域:", self.azure_region_combo)

        # TTS语音选择
        self.tts_voice_combo = QComboBox()
        voices = [
            ("zh-CN-XiaoxiaoNeural", "晓晓 (推荐)"),
            ("zh-CN-XiaoyiNeural", "晓伊"),
            ("zh-CN-YunxiNeural", "云希"),
            ("zh-CN-YunyangNeural", "云扬"),
            ("zh-CN-XiaochenNeural", "晓辰"),
            ("zh-CN-XiaohanNeural", "晓涵"),
            ("zh-CN-XiaomoNeural", "晓墨"),
            ("zh-CN-XiaoxuanNeural", "晓萱"),
            ("zh-CN-XiaoyanNeural", "晓颜"),
            ("zh-CN-XiaoyouNeural", "晓悠"),
        ]
        for voice_id, voice_name in voices:
            self.tts_voice_combo.addItem(f"{voice_name} ({voice_id})", voice_id)
        
        current_voice = self.config.get("tts_voice", "zh-CN-XiaoxiaoNeural")
        for i in range(self.tts_voice_combo.count()):
            if self.tts_voice_combo.itemData(i) == current_voice:
                self.tts_voice_combo.setCurrentIndex(i)
                break
        tts_layout.addRow("语音选择:", self.tts_voice_combo)

        # TTS语速设置
        self.tts_speed_slider = QSlider(Qt.Horizontal)
        self.tts_speed_slider.setMinimum(50)  # 0.5倍速
        self.tts_speed_slider.setMaximum(200)  # 2.0倍速
        speed_value = int(self.config.get("tts_speaking_rate", 1.0) * 100)
        self.tts_speed_slider.setValue(speed_value)
        self.tts_speed_slider.setTickPosition(QSlider.TicksBelow)
        self.tts_speed_slider.setTickInterval(25)
        
        self.tts_speed_label = QLabel(f"{speed_value/100:.1f}x")
        self.tts_speed_slider.valueChanged.connect(
            lambda value: self.tts_speed_label.setText(f"{value/100:.1f}x")
        )
        
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(self.tts_speed_slider)
        speed_layout.addWidget(self.tts_speed_label)
        tts_layout.addRow("语速设置:", speed_layout)

        tts_group.setLayout(tts_layout)

        # 添加所有组件到主布局
        layout.addWidget(api_group)
        layout.addWidget(browser_group)
        layout.addWidget(model_group)
        layout.addWidget(ui_group)
        layout.addWidget(tts_group)

        # 工具管理
        tool_group = QGroupBox("工具管理")
        tool_layout = QVBoxLayout()

        # 网站管理
        website_group = QGroupBox("网站管理")
        website_layout = QVBoxLayout()

        self.website_list = QListWidget()
        for site, url in self.config.get("website_map", {}).items():
            self.website_list.addItem(f"{site}: {url}")
        website_layout.addWidget(self.website_list)

        website_btn_layout = QHBoxLayout()
        add_website_btn = QPushButton("添加网站")
        add_website_btn.clicked.connect(self.add_website)
        remove_website_btn = QPushButton("移除网站")
        remove_website_btn.clicked.connect(self.remove_website)
        website_btn_layout.addWidget(add_website_btn)
        website_btn_layout.addWidget(remove_website_btn)

        website_layout.addLayout(website_btn_layout)
        website_group.setLayout(website_layout)

        # 应用管理
        app_group = QGroupBox("应用管理")
        app_layout = QVBoxLayout()

        self.app_list = QListWidget()
        for app, path in self.config.get("app_map", {}).items():
            self.app_list.addItem(f"{app}: {path}")
        app_layout.addWidget(self.app_list)

        app_btn_layout = QHBoxLayout()
        scan_apps_btn = QPushButton("扫描应用")
        scan_apps_btn.clicked.connect(self.scan_applications)
        add_app_btn = QPushButton("添加应用")
        add_app_btn.clicked.connect(self.add_application)
        remove_app_btn = QPushButton("移除应用")
        remove_app_btn.clicked.connect(self.remove_application)
        app_btn_layout.addWidget(scan_apps_btn)
        app_btn_layout.addWidget(add_app_btn)
        app_btn_layout.addWidget(remove_app_btn)

        app_layout.addLayout(app_btn_layout)
        app_group.setLayout(app_layout)

        tool_layout.addWidget(website_group)
        tool_layout.addWidget(app_group)
        tool_group.setLayout(tool_layout)

        # 按钮
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存设置")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)

        layout.addWidget(tool_group)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
    
    def on_transparency_changed(self, value):
        """透明度滑块值改变时的处理"""
        # 更新标签显示
        self.transparency_label.setText(f"{value}%")
        
        # 如果有回调函数，实时更新主窗口透明度
        if self.transparency_callback:
            try:
                self.transparency_callback(value)
            except Exception as e:
                print(f"⚠️ 实时更新透明度失败: {str(e)}")
    
    def add_website(self):
        """添加网站"""
        site, ok1 = QInputDialog.getText(self, "添加网站", "输入网站名称:")
        if not ok1 or not site:
            return

        url, ok2 = QInputDialog.getText(self, "添加网站", "输入网站URL:")
        if ok2 and url:
            self.website_list.addItem(f"{site}: {url}")

    def remove_website(self):
        """移除网站"""
        if self.website_list.currentRow() >= 0:
            self.website_list.takeItem(self.website_list.currentRow())

    def scan_applications(self):
        """扫描应用程序"""
        apps = scan_windows_apps()
        self.app_list.clear()
        for app_name, app_path in apps.items():
            self.app_list.addItem(f"{app_name}: {app_path}")

    def add_application(self):
        """添加应用程序"""
        app_name, ok1 = QInputDialog.getText(self, "添加应用", "输入应用名称:")
        if not ok1 or not app_name:
            return

        app_path, ok2 = QFileDialog.getOpenFileName(self, "选择应用程序", "",
                                                    "Executable Files (*.exe;*.lnk);;All Files (*)")
        if ok2 and app_path:
            self.app_list.addItem(f"{app_name}: {app_path}")

    def remove_application(self):
        """移除应用程序"""
        if self.app_list.currentRow() >= 0:
            self.app_list.takeItem(self.app_list.currentRow())

    def browse_default_save_path(self):
        """浏览默认保存路径"""
        current_path = self.default_save_path_edit.text().strip()
        if not current_path:
            current_path = "D:/"
        
        # 确保路径存在，如果不存在则创建
        if not os.path.exists(current_path):
            try:
                os.makedirs(current_path, exist_ok=True)
            except:
                current_path = "D:/"
        
        folder_path = QFileDialog.getExistingDirectory(
            self, 
            "选择默认保存路径", 
            current_path,
            QFileDialog.ShowDirsOnly
        )
        
        if folder_path:
            # 确保路径以斜杠结尾
            if not folder_path.endswith('/') and not folder_path.endswith('\\'):
                folder_path += '/'
            self.default_save_path_edit.setText(folder_path)

    def save_settings(self):
        """保存设置"""
        # 保存API密钥
        self.config["openai_key"] = self.openai_key_edit.text()
        self.config["deepseek_key"] = self.deepseek_key_edit.text()
        self.config["heweather_key"] = self.weather_key_edit.text()
        self.config["amap_key"] = self.amap_key_edit.text()

        # 保存天气数据来源设置
        self.config["weather_source"] = self.weather_source_combo.currentText()

        # 保存浏览器设置
        browser_text = self.default_browser_combo.currentText()
        if browser_text == "默认浏览器":
            self.config["default_browser"] = ""
        else:
            self.config["default_browser"] = browser_text
        self.config["default_search_engine"] = self.default_search_engine_combo.currentText()

        # 保存模型选择
        self.config["selected_model"] = self.chat_model_combo.currentText()
        
        # 保存识底深湖模型选择
        self.config["memory_summary_model"] = self.memory_model_combo.currentText()

        # 保存AI Token数设置
        try:
            max_tokens = int(self.max_tokens_edit.text())
            if max_tokens < 0:
                max_tokens = 0  # 0表示无限制
            self.config["max_tokens"] = max_tokens
        except ValueError:
            self.config["max_tokens"] = 1000  # 默认值

        # 保存窗口透明度设置
        self.config["window_transparency"] = self.transparency_slider.value()

        # 保存记忆系统设置
        self.config["show_remember_details"] = self.show_remember_details_checkbox.isChecked()

        # 保存AI智能创建后备机制设置
        self.config["ai_fallback_enabled"] = self.ai_fallback_checkbox.isChecked()

        # 保存AI智能总结设置
        self.config["ai_summary_enabled"] = self.ai_summary_checkbox.isChecked()

        # 保存默认保存路径设置
        self.config["default_save_path"] = self.default_save_path_edit.text().strip()

        # 保存笔记文件名格式设置
        filename_format_index = self.filename_format_combo.currentIndex()
        if filename_format_index == 1:  # 简单格式
            self.config["note_filename_format"] = "simple"
        else:  # 时间戳格式
            self.config["note_filename_format"] = "timestamp"

        # 保存TTS设置
        self.config["tts_enabled"] = self.tts_enabled_checkbox.isChecked()
        self.config["azure_tts_key"] = self.azure_tts_key_edit.text()
        
        # 保存Azure区域
        region_text = self.azure_region_combo.currentText()
        self.config["azure_region"] = self._get_region_code(region_text)
        
        # 保存TTS语音
        voice_index = self.tts_voice_combo.currentIndex()
        if voice_index >= 0:
            self.config["tts_voice"] = self.tts_voice_combo.itemData(voice_index)
        
        # 保存TTS语速
        speed_value = self.tts_speed_slider.value() / 100.0
        self.config["tts_speaking_rate"] = speed_value

        # 保存网站映射
        website_map = {}
        for i in range(self.website_list.count()):
            item_text = self.website_list.item(i).text()
            if ": " in item_text:
                site, url = item_text.split(": ", 1)
                website_map[site] = url
        self.config["website_map"] = website_map

        # 保存应用映射
        app_map = {}
        for i in range(self.app_list.count()):
            item_text = self.app_list.item(i).text()
            if ": " in item_text:
                app, path = item_text.split(": ", 1)
                app_map[app] = path
        self.config["app_map"] = app_map

        # 保存到文件
        save_config(self.config)
        self.accept()
    
    def _get_region_name(self, region_code: str) -> str:
        """获取区域名称"""
        region_names = {
            "eastasia": "东亚",
            "southeastasia": "东南亚",
            "eastus": "美国东部",
            "westus": "美国西部",
            "northeurope": "北欧",
            "westeurope": "西欧"
        }
        return region_names.get(region_code, region_code)
    
    def _get_region_code(self, region_text: str) -> str:
        """从区域文本中提取区域代码"""
        return region_text.split(" ")[0]


class MemoryLakeDialog(QDialog):
    """识底深湖记忆系统对话框"""
    
    def __init__(self, memory_lake, parent=None):
        super().__init__(parent)
        self.memory_lake = memory_lake
        self.setWindowTitle("识底深湖 - 记忆系统")
        self.setGeometry(200, 200, 800, 700)  # 增加窗口高度
        
        # 设置图标
        if os.path.exists("icon.ico"):
            self.setWindowIcon(QIcon("icon.ico"))
        
        self.init_ui()
        self.refresh_data()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 统计信息区域
        stats_group = QGroupBox("记忆统计")
        stats_group.setStyleSheet("""
            QGroupBox {
                color: #cdd6f4;
                font-size: 14px;
                border: 1px solid #45475a;
                border-radius: 5px;
                margin-top: 1ex;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: #1e1e2e;
            }
        """)
        stats_layout = QHBoxLayout()
        
        self.stats_label = QLabel("加载中...")
        self.stats_label.setStyleSheet("color: #a6e3a1; font-size: 12px;")
        stats_layout.addWidget(self.stats_label)
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e1e;
                border-radius: 5px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #74c7ec;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_data)
        stats_layout.addWidget(refresh_btn)
        
        stats_group.setLayout(stats_layout)
        
        # 主题索引区域
        topics_group = QGroupBox("主题索引")
        topics_group.setStyleSheet("""
            QGroupBox {
                color: #cdd6f4;
                font-size: 14px;
                border: 1px solid #45475a;
                border-radius: 5px;
                margin-top: 2ex;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: #1e1e2e;
            }
        """)
        topics_layout = QVBoxLayout()
        
        # 搜索框
        search_layout = QHBoxLayout()
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索主题...")
        self.search_edit.setStyleSheet("""
            QLineEdit {
                background-color: #313244;
                color: #cdd6f4;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 12px;
            }
        """)
        self.search_edit.textChanged.connect(self.filter_topics)
        search_layout.addWidget(self.search_edit)
        
        topics_layout.addLayout(search_layout)
        
        # 添加一些间距，避免标题被遮挡
        topics_layout.addSpacing(10)
        
        # 主题列表
        self.topics_list = QListWidget()
        self.topics_list.setStyleSheet("""
            QListWidget {
                background-color: #313244;
                color: #cdd6f4;
                border-radius: 5px;
                padding: 5px;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #45475a;
            }
            QListWidget::item:selected {
                background-color: #89b4fa;
                color: #1e1e1e;
            }
        """)
        self.topics_list.itemClicked.connect(self.show_topic_details)
        topics_layout.addWidget(self.topics_list)
        
        topics_group.setLayout(topics_layout)
        
        # 详情区域
        details_group = QGroupBox("主题详情")
        details_group.setStyleSheet("""
            QGroupBox {
                color: #cdd6f4;
                font-size: 14px;
                border: 1px solid #45475a;
                border-radius: 5px;
                margin-top: 2ex;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: #1e1e2e;
            }
        """)
        details_layout = QVBoxLayout()
        
        # 重点记忆标签区域
        important_layout = QHBoxLayout()
        
        self.important_label = QLabel("⭐ 重点记忆")
        self.important_label.setStyleSheet("""
            QLabel {
                color: #f9e2af;
                font-weight: bold;
                font-size: 12px;
                padding: 5px 10px;
                background-color: #313244;
                border-radius: 5px;
                border: 1px solid #f9e2af;
            }
        """)
        self.important_label.setVisible(False)
        
        self.important_btn = QPushButton("标记为重点记忆")
        self.important_btn.setStyleSheet("""
            QPushButton {
                background-color: #f9e2af;
                color: #1e1e1e;
                border-radius: 5px;
                padding: 5px 10px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #fab387;
            }
        """)
        self.important_btn.clicked.connect(self.toggle_important_memory)
        self.important_btn.setVisible(False)
        
        important_layout.addStretch()
        important_layout.addWidget(self.important_label)
        important_layout.addWidget(self.important_btn)
        
        details_layout.addLayout(important_layout)
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setStyleSheet("""
            QTextEdit {
                background-color: #313244;
                color: #cdd6f4;
                border-radius: 5px;
                padding: 10px;
                font-size: 12px;
            }
        """)
        details_layout.addWidget(self.details_text)
        
        # 添加一些间距，避免标题被遮挡
        details_layout.addSpacing(10)
        
        details_group.setLayout(details_layout)
        
        # 添加到主布局
        layout.addWidget(stats_group)
        layout.addWidget(topics_group, 2)
        layout.addWidget(details_group, 1)
        
        self.setLayout(layout)
    
    def refresh_data(self):
        """刷新记忆数据"""
        stats = self.memory_lake.get_memory_stats()
        self.stats_label.setText(
            f"总主题数: {stats['total_topics']} | "
            f"重点记忆: {stats['important_topics']} | "
            f"日志文件数: {stats['total_log_files']} | "
            f"记忆文件大小: {stats['memory_file_size']} bytes"
        )
        
        self.load_topics()
    
    def load_topics(self):
        """加载主题列表"""
        self.topics_list.clear()
        try:
            topics = self.memory_lake.memory_index.get("topics", [])
            
            for topic in reversed(topics):  # 最新的在前面
                if isinstance(topic, dict) and 'date' in topic and 'timestamp' in topic and 'topic' in topic:
                    # 添加重点记忆标识
                    important_icon = "⭐ " if topic.get("is_important", False) else ""
                    item_text = f"{important_icon}[{topic['date']} {topic['timestamp']}] {topic['topic']}"
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.UserRole, topic)
                    self.topics_list.addItem(item)
        except Exception as e:
            print(f"加载主题列表失败: {str(e)}")
    
    def filter_topics(self):
        """过滤主题"""
        search_text = self.search_edit.text().lower()
        for i in range(self.topics_list.count()):
            item = self.topics_list.item(i)
            item.setHidden(search_text not in item.text().lower())
    
    def show_topic_details(self, item):
        """显示主题详情"""
        topic_data = item.data(Qt.UserRole)
        if not topic_data:
            return
        
        # 显示重点记忆标签
        is_important = topic_data.get("is_important", False)
        self.important_label.setVisible(is_important)
        self.important_btn.setVisible(True)
        
        if is_important:
            self.important_btn.setText("取消重点记忆")
            self.important_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f38ba8;
                    color: #1e1e1e;
                    border-radius: 5px;
                    padding: 5px 10px;
                    font-weight: bold;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #eba0ac;
                }
            """)
        else:
            self.important_btn.setText("标记为重点记忆")
            self.important_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f9e2af;
                    color: #1e1e1e;
                    border-radius: 5px;
                    padding: 5px 10px;
                    font-weight: bold;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #fab387;
                }
            """)
        
        # 保存当前选中的主题索引
        topics = self.memory_lake.memory_index.get("topics", [])
        # 由于UI显示是倒序（最新在前），但存储是正序，需要转换索引
        reversed_topics = list(reversed(topics))
        ui_index = reversed_topics.index(topic_data)
        self.current_topic_index = len(topics) - 1 - ui_index
        
        details = f"主题: {topic_data['topic']}\n"
        details += f"日期: {topic_data['date']}\n"
        details += f"时间: {topic_data['timestamp']}\n"
        details += f"日志文件: {topic_data.get('log_file', 'N/A')}\n"
        
        # 添加具体聊天记录
        conversation_details = topic_data.get('conversation_details', '')
        if conversation_details:
            details += f"\n具体聊天记录:\n{conversation_details}"
        
        self.details_text.setText(details)

    def toggle_important_memory(self):
        """切换重点记忆标记"""
        if not hasattr(self, 'current_topic_index'):
            return
        
        try:
            topics = self.memory_lake.memory_index.get("topics", [])
            if 0 <= self.current_topic_index < len(topics):
                current_topic = topics[self.current_topic_index]
                is_important = current_topic.get("is_important", False)
                
                if is_important:
                    # 取消重点记忆标记
                    if self.memory_lake.unmark_as_important(self.current_topic_index):
                        self.refresh_data()
                        print("✅ 已取消重点记忆标记")
                else:
                    # 添加重点记忆标记
                    if self.memory_lake.mark_as_important(self.current_topic_index):
                        self.refresh_data()
                        print("✅ 已标记为重点记忆")
        except Exception as e:
            print(f"切换重点记忆标记失败: {str(e)}")


class MCPToolsDialog(QDialog):
    """MCP工具管理对话框"""
    
    def __init__(self, mcp_tools, parent=None):
        super().__init__(parent)
        self.mcp_tools = mcp_tools
        self.setWindowTitle("MCP工具管理")
        self.setGeometry(200, 200, 1000, 800)  # 增加窗口高度
        
        # 设置图标
        if os.path.exists("icon.ico"):
            self.setWindowIcon(QIcon("icon.ico"))
        
        self.init_ui()
        self.refresh_tools()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 工具列表区域
        tools_group = QGroupBox("可用工具")
        tools_group.setStyleSheet("""
            QGroupBox {
                color: #cdd6f4;
                font-size: 14px;
                border: 1px solid #45475a;
                border-radius: 5px;
                margin-top: 2ex;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: #1e1e2e;
            }
        """)
        tools_layout = QVBoxLayout()
        
        # 搜索框和按钮区域
        search_layout = QHBoxLayout()
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索工具...")
        self.search_edit.setStyleSheet("""
            QLineEdit {
                background-color: #313244;
                color: #cdd6f4;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 12px;
            }
        """)
        self.search_edit.textChanged.connect(self.filter_tools)
        search_layout.addWidget(self.search_edit)
        
        # 按钮区域
        refresh_btn = QPushButton("刷新")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e1e;
                border-radius: 5px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #74c7ec;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_tools)
        search_layout.addWidget(refresh_btn)
        
        add_tool_btn = QPushButton("新建工具")
        add_tool_btn.setStyleSheet("""
            QPushButton {
                background-color: #f38ba8;
                color: #1e1e1e;
                border-radius: 5px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #eba0ac;
            }
        """)
        add_tool_btn.clicked.connect(self.add_new_tool)
        search_layout.addWidget(add_tool_btn)
        
        tools_layout.addLayout(search_layout)
        
        # 添加一些间距，避免标题被遮挡
        tools_layout.addSpacing(10)
        
        # 工具列表
        self.tools_list = QListWidget()
        self.tools_list.setStyleSheet("""
            QListWidget {
                background-color: #313244;
                color: #cdd6f4;
                border-radius: 5px;
                padding: 5px;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #45475a;
            }
            QListWidget::item:selected {
                background-color: #89b4fa;
                color: #1e1e1e;
            }
        """)
        self.tools_list.itemClicked.connect(self.show_tool_details)
        tools_layout.addWidget(self.tools_list)
        
        tools_group.setLayout(tools_layout)
        
        # 工具详情区域
        details_group = QGroupBox("工具详情")
        details_group.setStyleSheet("""
            QGroupBox {
                color: #cdd6f4;
                font-size: 14px;
                border: 1px solid #45475a;
                border-radius: 5px;
                margin-top: 2ex;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: #1e1e2e;
            }
        """)
        details_layout = QVBoxLayout()
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setStyleSheet("""
            QTextEdit {
                background-color: #313244;
                color: #cdd6f4;
                border-radius: 5px;
                padding: 10px;
                font-size: 12px;
            }
        """)
        details_layout.addWidget(self.details_text)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.test_btn = QPushButton("测试工具")
        self.test_btn.setStyleSheet("""
            QPushButton {
                background-color: #a6e3a1;
                color: #1e1e1e;
                border-radius: 5px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #94e2d5;
            }
        """)
        self.test_btn.clicked.connect(self.test_tool)
        button_layout.addWidget(self.test_btn)
        
        self.edit_btn = QPushButton("编辑工具")
        self.edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #f9e2af;
                color: #1e1e1e;
                border-radius: 5px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #fab387;
            }
        """)
        self.edit_btn.clicked.connect(self.edit_tool)
        button_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("删除工具")
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f38ba8;
                color: #1e1e1e;
                border-radius: 5px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #eba0ac;
            }
        """)
        self.delete_btn.clicked.connect(self.delete_tool)
        button_layout.addWidget(self.delete_btn)
        
        details_layout.addLayout(button_layout)
        details_group.setLayout(details_layout)
        
        # 使用QSplitter来更好地控制布局
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(tools_group)
        splitter.addWidget(details_group)
        splitter.setSizes([600, 400])  # 设置初始大小比例
        
        layout.addWidget(splitter)
        
        self.setLayout(layout)
    
    def refresh_tools(self):
        """刷新工具列表"""
        try:
            # 使用同步方法获取工具列表
            tools = self.mcp_tools.list_tools()
            
            self.tools_list.clear()
            
            # 添加内置工具
            for tool in tools:
                item = QListWidgetItem(f"🔧 {tool}")
                item.setData(Qt.UserRole, tool)
                item.setData(Qt.UserRole + 1, "builtin")  # 标记为内置工具
                self.tools_list.addItem(item)
            
            # 添加自定义工具
            custom_tools = self.load_custom_tools()
            for tool_name in custom_tools.keys():
                item = QListWidgetItem(f"⚙️ {tool_name}")
                item.setData(Qt.UserRole, tool_name)
                item.setData(Qt.UserRole + 1, "custom")  # 标记为自定义工具
                self.tools_list.addItem(item)
                
        except Exception as e:
            print(f"刷新工具列表失败: {str(e)}")
    
    def filter_tools(self):
        """过滤工具"""
        search_text = self.search_edit.text().lower()
        for i in range(self.tools_list.count()):
            item = self.tools_list.item(i)
            item.setHidden(search_text not in item.text().lower())
    
    def show_tool_details(self, item):
        """显示工具详情"""
        tool_name = item.data(Qt.UserRole)
        tool_type = item.data(Qt.UserRole + 1)
        if not tool_name:
            return
        
        try:
            details = f"工具名称: {tool_name}\n"
            details += f"工具类型: {'内置工具' if tool_type == 'builtin' else '自定义工具'}\n"
            
            if tool_type == "builtin":
                # 内置工具 - 现在允许编辑
                info = self.mcp_tools.server.get_tool_info(tool_name)
                if info:
                    details += f"描述: {info.get('description', '无描述')}\n"
                else:
                    details += "描述: 无描述\n"
                details += "注意: 内置工具可以编辑，编辑后会创建自定义版本\n"
            else:
                # 自定义工具
                custom_tools = self.load_custom_tools()
                if tool_name in custom_tools:
                    tool_info = custom_tools[tool_name]
                    details += f"描述: {tool_info.get('description', '无描述')}\n"
                    details += f"代码长度: {len(tool_info.get('code', ''))} 字符\n"
                else:
                    details += "描述: 无描述\n"
            
            self.details_text.setText(details)
        except Exception as e:
            self.details_text.setText(f"获取工具信息失败: {str(e)}")
    
    def test_tool(self):
        """测试选中的工具"""
        current_item = self.tools_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请先选择一个工具")
            return
        
        tool_name = current_item.data(Qt.UserRole)
        if not tool_name:
            return
        
        # 根据工具类型提供不同的测试参数
        test_params = self.get_test_params(tool_name)
        
        try:
            # 使用同步方法调用工具
            result = self.mcp_tools.server.call_tool(tool_name, **test_params)
            QMessageBox.information(self, "测试结果", f"工具 {tool_name} 测试结果:\n\n{result}")
        except Exception as e:
            QMessageBox.warning(self, "测试失败", f"测试工具失败: {str(e)}")
    
    def get_test_params(self, tool_name):
        """获取工具的测试参数"""
        test_params = {
            "get_system_info": {},
            "list_files": {"directory": "."},
            "read_file": {"file_path": "README.md"},
            "write_file": {"file_path": "test.txt", "content": "测试内容"},
            "execute_command": {"command": "echo Hello World"},
            "get_process_list": {},
            "create_note": {"title": "测试笔记", "content": "这是一个测试笔记"},
            "list_notes": {},
            "search_notes": {"keyword": "测试"},
            "get_weather_info": {"city": "北京"},
            "calculate_distance": {"location1": "北京", "location2": "上海"},
            "calculate": {"expression": "2+2"},
            "get_memory_stats": {},
            "高德mcp": {"location1": "北京", "location2": "上海"}
        }
        
        return test_params.get(tool_name, {})
    
    def add_new_tool(self):
        """新建工具"""
        dialog = AddToolDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            tool_name = dialog.tool_name_edit.text().strip()
            tool_description = dialog.tool_description_edit.toPlainText().strip()
            tool_code = dialog.tool_code_edit.toPlainText().strip()
            
            if tool_name and tool_code:
                # 保存到自定义工具文件
                self.save_custom_tool(tool_name, tool_description, tool_code)
                self.refresh_tools()
                QMessageBox.information(self, "成功", f"工具 '{tool_name}' 已创建")
    
    def edit_tool(self):
        """编辑工具"""
        current_item = self.tools_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请先选择一个工具")
            return
        
        tool_name = current_item.data(Qt.UserRole)
        tool_type = current_item.data(Qt.UserRole + 1)
        if not tool_name:
            return
        
        if tool_type == "custom":
            # 自定义工具
            custom_tools = self.load_custom_tools()
            if tool_name in custom_tools:
                tool_info = custom_tools[tool_name]
                dialog = AddToolDialog(self, tool_name, tool_info['description'], tool_info['code'])
                if dialog.exec_() == QDialog.Accepted:
                    new_name = dialog.tool_name_edit.text().strip()
                    new_description = dialog.tool_description_edit.toPlainText().strip()
                    new_code = dialog.tool_code_edit.toPlainText().strip()
                    
                    if new_name and new_code:
                        # 删除旧工具，保存新工具
                        self.delete_custom_tool(tool_name)
                        self.save_custom_tool(new_name, new_description, new_code)
                        self.refresh_tools()
                        QMessageBox.information(self, "成功", f"工具 '{tool_name}' 已更新")
        else:
            # 内置工具 - 现在允许编辑
            try:
                # 获取内置工具的代码
                builtin_code = self.get_builtin_tool_code(tool_name)
                if builtin_code:
                    dialog = AddToolDialog(self, tool_name, f"内置工具: {tool_name}", builtin_code)
                    if dialog.exec_() == QDialog.Accepted:
                        new_code = dialog.tool_code_edit.toPlainText().strip()
                        if new_code:
                            # 更新内置工具代码
                            self.update_builtin_tool_code(tool_name, new_code)
                            self.refresh_tools()
                            QMessageBox.information(self, "成功", f"内置工具 '{tool_name}' 已更新")
                else:
                    QMessageBox.warning(self, "警告", f"无法获取内置工具 '{tool_name}' 的代码")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"编辑内置工具失败: {str(e)}")
    
    def get_builtin_tool_code(self, tool_name):
        """获取内置工具的代码"""
        try:
            # 这里可以根据工具名称返回对应的代码模板
            if tool_name == "calculate_distance":
                return '''def calculate_distance(location1, location2):
    """计算两个地点之间的距离（使用高德地图API）"""
    try:
        # 高德地图API密钥 - 直接从配置文件读取最新值
        api_key = self.get_latest_amap_key()
        if not api_key or api_key == "mykey":
            return "高德地图API密钥未配置，请在设置中配置高德地图API密钥"
        
        # 地理编码API获取坐标
        def get_coordinates(address):
            url = "https://restapi.amap.com/v3/geocode/geo"
            params = {
                "address": address,
                "key": api_key,
                "output": "json"
            }
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data["status"] == "1" and data["geocodes"]:
                location = data["geocodes"][0]["location"]
                return location.split(",")
            return None
        
        # 获取两个地点的坐标
        coords1 = get_coordinates(location1)
        coords2 = get_coordinates(location2)
        
        if not coords1 or not coords2:
            return f"无法获取地点坐标：{location1} 或 {location2}"
        
        # 计算直线距离
        from math import radians, cos, sin, asin, sqrt
        
        def haversine_distance(lat1, lon1, lat2, lon2):
            """使用Haversine公式计算两点间的直线距离"""
            # 将经纬度转换为弧度
            lat1, lon1, lat2, lon2 = map(radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
            
            # Haversine公式
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            r = 6371  # 地球半径（公里）
            return c * r
        
        distance = haversine_distance(coords1[1], coords1[0], coords2[1], coords2[0])
        
        result = {
            "location1": location1,
            "location2": location2,
            "coordinates1": coords1,
            "coordinates2": coords2,
            "distance_km": round(distance, 2),
            "distance_m": round(distance * 1000, 0),
            "calculation_type": "直线距离（Haversine公式）",
            "update_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return f"计算距离失败: {str(e)}"'''
            else:
                return f"# 内置工具 {tool_name} 的代码\n# 请在此处编辑代码"
        except:
            return None
    
    def update_builtin_tool_code(self, tool_name, new_code):
        """更新内置工具代码"""
        try:
            # 这里可以更新内置工具的代码
            # 由于内置工具是硬编码的，我们可以将修改后的代码保存到自定义工具中
            custom_tools = self.load_custom_tools()
            custom_tools[f"{tool_name}_modified"] = {
                "description": f"修改后的{tool_name}工具",
                "code": new_code,
                "type": "custom"
            }
            
            with open("custom_tools.json", "w", encoding="utf-8") as f:
                json.dump(custom_tools, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            raise Exception(f"更新内置工具代码失败: {str(e)}")
    
    def delete_tool(self):
        """删除工具"""
        current_item = self.tools_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请先选择一个工具")
            return
        
        tool_name = current_item.data(Qt.UserRole)
        tool_type = current_item.data(Qt.UserRole + 1)
        if not tool_name:
            return
        
        if tool_type == "custom":
            # 自定义工具
            custom_tools = self.load_custom_tools()
            if tool_name in custom_tools:
                reply = QMessageBox.question(self, "确认删除", f"确定要删除工具 '{tool_name}' 吗？",
                                           QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self.delete_custom_tool(tool_name)
                    self.refresh_tools()
                    QMessageBox.information(self, "成功", f"工具 '{tool_name}' 已删除")
        else:
            QMessageBox.information(self, "提示", "内置工具无法删除")
    
    def save_custom_tool(self, tool_name, description, code):
        """保存自定义工具"""
        custom_tools = self.load_custom_tools()
        custom_tools[tool_name] = {
            "description": description,
            "code": code,
            "type": "custom"
        }
        
        # 检查代码中是否有API密钥，如果有则同步到配置文件
        import re
        api_key_pattern = r'["\']([a-f0-9]{32})["\']'
        api_keys = re.findall(api_key_pattern, code)
        
        if api_keys:
            # 使用第一个找到的API密钥
            api_key = api_keys[0]
            try:
                if os.path.exists("ai_agent_config.json"):
                    with open("ai_agent_config.json", "r", encoding="utf-8") as f:
                        config = json.load(f)
                    
                    # 更新高德地图API密钥
                    config["amap_key"] = api_key
                    
                    # 保存更新后的配置
                    with open("ai_agent_config.json", "w", encoding="utf-8") as f:
                        json.dump(config, f, ensure_ascii=False, indent=2)
                    
                    # 同时更新config.py中的默认值（如果存在）
                    self.update_config_py_amap_key(api_key)
                    
                    print(f"✅ 已自动同步API密钥到配置文件: {api_key}")
            except Exception as e:
                print(f"⚠️ 同步API密钥失败: {str(e)}")
        
        with open("custom_tools.json", "w", encoding="utf-8") as f:
            json.dump(custom_tools, f, ensure_ascii=False, indent=2)
    
    def delete_custom_tool(self, tool_name):
        """删除自定义工具"""
        custom_tools = self.load_custom_tools()
        if tool_name in custom_tools:
            del custom_tools[tool_name]
            with open("custom_tools.json", "w", encoding="utf-8") as f:
                json.dump(custom_tools, f, ensure_ascii=False, indent=2)
    
    def get_latest_amap_key(self):
        """获取最新的高德地图API密钥"""
        try:
            # 直接从配置文件读取最新值
            if os.path.exists("ai_agent_config.json"):
                with open("ai_agent_config.json", "r", encoding="utf-8") as f:
                    config = json.load(f)
                    api_key = config.get("amap_key", "")
                    # 如果API密钥为空或为占位符，返回空字符串
                    if not api_key or api_key == "MYKEY" or api_key == "mykey":
                        return ""
                    return api_key
        except Exception as e:
            print(f"读取高德地图API密钥失败: {str(e)}")
        return ""

    def update_config_py_amap_key(self, api_key):
        """更新config.py中的amap_key默认值"""
        try:
            if os.path.exists("config.py"):
                with open("config.py", "r", encoding="utf-8") as f:
                    content = f.read()
                
                # 使用正则表达式更新amap_key的默认值
                import re
                # 匹配 "amap_key": "" 或 "amap_key": "任意内容"
                pattern = r'"amap_key":\s*"[^"]*"'
                replacement = f'"amap_key": "{api_key}"'
                
                new_content = re.sub(pattern, replacement, content)
                
                # 写回文件
                with open("config.py", "w", encoding="utf-8") as f:
                    f.write(new_content)
                
                print(f"✅ 已同步更新config.py中的amap_key默认值: {api_key}")
        except Exception as e:
            print(f"⚠️ 更新config.py失败: {str(e)}")

    def load_custom_tools(self):
        """加载自定义工具"""
        try:
            if os.path.exists("custom_tools.json"):
                with open("custom_tools.json", "r", encoding="utf-8") as f:
                    return json.load(f)
        except:
            pass
        return {}


class AddToolDialog(QDialog):
    """新建工具对话框"""
    
    def __init__(self, parent=None, tool_name="", description="", code=""):
        super().__init__(parent)
        self.setWindowTitle("新建工具")
        self.setGeometry(300, 300, 600, 500)
        
        # 从代码中提取API密钥
        self.extracted_api_key = self.extract_api_key_from_code(code)
        
        self.init_ui(tool_name, description, code)
    
    def extract_api_key_from_code(self, code):
        """从代码中提取API密钥"""
        if not code:
            return ""
        
        # 查找常见的API密钥模式
        import re
        
        # 查找双引号包围的API密钥
        double_quote_pattern = r'api_key\s*=\s*"([^"]+)"'
        match = re.search(double_quote_pattern, code)
        if match and match.group(1) != "mykey":
            return match.group(1)
        
        # 查找单引号包围的API密钥
        single_quote_pattern = r"api_key\s*=\s*'([^']+)'"
        match = re.search(single_quote_pattern, code)
        if match and match.group(1) != "mykey":
            return match.group(1)
        
        return ""
    
    def update_config_py_amap_key(self, api_key):
        """更新config.py中的amap_key默认值"""
        try:
            if os.path.exists("config.py"):
                with open("config.py", "r", encoding="utf-8") as f:
                    content = f.read()
                
                # 使用正则表达式更新amap_key的默认值
                import re
                # 匹配 "amap_key": "" 或 "amap_key": "任意内容"
                pattern = r'"amap_key":\s*"[^"]*"'
                replacement = f'"amap_key": "{api_key}"'
                
                new_content = re.sub(pattern, replacement, content)
                
                # 写回文件
                with open("config.py", "w", encoding="utf-8") as f:
                    f.write(new_content)
                
                print(f"✅ 已同步更新config.py中的amap_key默认值: {api_key}")
        except Exception as e:
            print(f"⚠️ 更新config.py失败: {str(e)}")
    
    def init_ui(self, tool_name, description, code):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 工具名称
        name_layout = QHBoxLayout()
        name_label = QLabel("工具名称:")
        name_label.setStyleSheet("color: #cdd6f4; font-size: 12px;")
        self.tool_name_edit = QLineEdit(tool_name)
        self.tool_name_edit.setStyleSheet("""
            QLineEdit {
                background-color: #313244;
                color: #cdd6f4;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 12px;
            }
        """)
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.tool_name_edit)
        
        # 工具描述
        desc_label = QLabel("工具描述:")
        desc_label.setStyleSheet("color: #cdd6f4; font-size: 12px;")
        self.tool_description_edit = QTextEdit(description)
        self.tool_description_edit.setMaximumHeight(80)
        self.tool_description_edit.setStyleSheet("""
            QTextEdit {
                background-color: #313244;
                color: #cdd6f4;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 12px;
            }
        """)
        
        # 工具代码
        code_label = QLabel("工具代码 (Python函数):")
        code_label.setStyleSheet("color: #cdd6f4; font-size: 12px;")
        
        # 代码编辑区域
        code_layout = QVBoxLayout()
        
        # 快速添加API按钮
        api_layout = QHBoxLayout()
        api_label = QLabel("快速添加API密钥:")
        api_label.setStyleSheet("color: #cdd6f4; font-size: 12px;")
        
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("输入API密钥，将自动替换代码中的'mykey'")
        # 如果从代码中提取到了API密钥，则显示在输入框中
        if self.extracted_api_key:
            self.api_key_edit.setText(self.extracted_api_key)
        self.api_key_edit.setStyleSheet("""
            QLineEdit {
                background-color: #313244;
                color: #cdd6f4;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 12px;
            }
        """)
        
        self.add_api_btn = QPushButton("替换API密钥")
        self.add_api_btn.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e1e;
                border-radius: 5px;
                padding: 5px 10px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #74c7ec;
            }
        """)
        self.add_api_btn.clicked.connect(self.replace_api_key)
        
        api_layout.addWidget(api_label)
        api_layout.addWidget(self.api_key_edit)
        api_layout.addWidget(self.add_api_btn)
        
        self.tool_code_edit = QTextEdit(code)
        self.tool_code_edit.setStyleSheet("""
            QTextEdit {
                background-color: #313244;
                color: #cdd6f4;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 12px;
                font-family: 'Consolas', 'Monaco', monospace;
            }
        """)
        
        code_layout.addLayout(api_layout)
        code_layout.addWidget(self.tool_code_edit)
        
        # 示例代码
        if not code:
            example_code = '''def my_custom_tool(param1="", param2=""):
    """
    自定义工具示例
    参数:
        param1: 第一个参数
        param2: 第二个参数
    返回:
        字符串结果
    """
    try:
        # 在这里编写你的工具逻辑
        result = f"参数1: {param1}, 参数2: {param2}"
        return f"工具执行成功: {result}"
    except Exception as e:
        return f"工具执行失败: {str(e)}"'''
            self.tool_code_edit.setPlainText(example_code)
        
        # 按钮
        button_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #a6e3a1;
                color: #1e1e1e;
                border-radius: 5px;
                padding: 5px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #94e2d5;
            }
        """)
        save_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f38ba8;
                color: #1e1e1e;
                border-radius: 5px;
                padding: 5px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #eba0ac;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        # 添加到主布局
        layout.addLayout(name_layout)
        layout.addWidget(desc_label)
        layout.addWidget(self.tool_description_edit)
        layout.addWidget(code_label)
        layout.addLayout(code_layout)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def replace_api_key(self):
        """替换代码中的API密钥"""
        api_key = self.api_key_edit.text().strip()
        if not api_key:
            QMessageBox.warning(self, "警告", "请输入API密钥")
            return
        
        current_code = self.tool_code_edit.toPlainText()
        
        # 检查是否有mykey占位符或现有的API密钥
        has_mykey = "mykey" in current_code.lower()
        
        # 检查是否有任何看起来像API密钥的字符串（32位字符）
        import re
        api_key_pattern = r'["\']([a-f0-9]{32})["\']'
        existing_api_keys = re.findall(api_key_pattern, current_code)
        
        if not has_mykey and not existing_api_keys:
            QMessageBox.information(self, "提示", "代码中没有找到'mykey'占位符或现有API密钥")
            return
        
        # 替换所有的"mykey"和现有API密钥为新的API密钥
        new_code = current_code
        if has_mykey:
            new_code = new_code.replace('"mykey"', f'"{api_key}"')
            new_code = new_code.replace("'mykey'", f"'{api_key}'")
            new_code = new_code.replace('"MYKEY"', f'"{api_key}"')
            new_code = new_code.replace("'MYKEY'", f"'{api_key}'")
        
        # 替换所有找到的API密钥
        for old_api_key in existing_api_keys:
            new_code = new_code.replace(f'"{old_api_key}"', f'"{api_key}"')
            new_code = new_code.replace(f"'{old_api_key}'", f"'{api_key}'")
        
        self.tool_code_edit.setPlainText(new_code)
        
        # 同时更新配置文件中的API密钥
        try:
            if os.path.exists("ai_agent_config.json"):
                with open("ai_agent_config.json", "r", encoding="utf-8") as f:
                    config = json.load(f)
                
                # 更新高德地图API密钥
                config["amap_key"] = api_key
                
                # 保存更新后的配置
                with open("ai_agent_config.json", "w", encoding="utf-8") as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
                
                # 同时更新config.py中的默认值
                self.update_config_py_amap_key(api_key)
                
                QMessageBox.information(self, "成功", f"已成功将代码中的API密钥替换为: {api_key}\n同时已更新配置文件中的高德地图API密钥")
            else:
                QMessageBox.information(self, "成功", f"已成功将代码中的API密钥替换为: {api_key}")
        except Exception as e:
            QMessageBox.warning(self, "警告", f"代码替换成功，但配置文件更新失败: {str(e)}")
