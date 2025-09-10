# -*- coding: utf-8 -*-
"""
Azure TTS管理器
处理文本转语音功能
"""

import asyncio
import threading
import queue
import time
from typing import Optional, Callable
import pygame
import tempfile
import os

try:
    import azure.cognitiveservices.speech as speechsdk
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    print("⚠️ Azure Speech SDK未安装，TTS功能将不可用")

class TTSManager:
    """Azure TTS管理器"""
    
    def __init__(self, azure_key: str = "", region: str = "eastasia"):
        self.azure_key = azure_key
        self.region = region
        self.enabled = False
        self.voice_name = "zh-CN-XiaoxiaoNeural"  # 默认女声
        self.speech_config = None
        self.audio_queue = queue.Queue()
        self.is_playing = False
        self.stop_playback = False
        
        # 初始化pygame音频
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.audio_available = True
        except Exception as e:
            print(f"⚠️ 音频初始化失败: {e}")
            self.audio_available = False
        
        # 初始化Azure配置
        if AZURE_AVAILABLE and azure_key:
            self._init_azure_config()
    
    def _init_azure_config(self):
        """初始化Azure配置"""
        try:
            self.speech_config = speechsdk.SpeechConfig(
                subscription=self.azure_key, 
                region=self.region
            )
            self.speech_config.speech_synthesis_voice_name = self.voice_name
            self.speech_config.speech_synthesis_speaking_rate = 1.0  # 语速
            self.enabled = True
            print("✅ Azure TTS配置成功")
        except Exception as e:
            print(f"❌ Azure TTS配置失败: {e}")
            self.enabled = False
    
    def update_config(self, azure_key: str, region: str):
        """更新Azure配置"""
        self.azure_key = azure_key
        self.region = region
        if azure_key:
            self._init_azure_config()
        else:
            self.enabled = False
    
    def set_voice(self, voice_name: str):
        """设置语音"""
        self.voice_name = voice_name
        if self.speech_config:
            self.speech_config.speech_synthesis_voice_name = voice_name
    
    def set_speaking_rate(self, rate: float):
        """设置语速 (0.5-2.0)"""
        if self.speech_config:
            self.speech_config.speech_synthesis_speaking_rate = rate
    
    def synthesize_text(self, text: str) -> Optional[str]:
        """合成文本为音频文件"""
        if not self.enabled or not AZURE_AVAILABLE:
            return None
        
        try:
            # 创建临时音频文件
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_file.close()
            
            # 配置音频输出
            audio_config = speechsdk.audio.AudioOutputConfig(filename=temp_file.name)
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config, 
                audio_config=audio_config
            )
            
            # 合成语音
            result = synthesizer.speak_text_async(text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                print(f"✅ TTS合成成功: {text[:50]}...")
                return temp_file.name
            else:
                print(f"❌ TTS合成失败: {result.reason}")
                os.unlink(temp_file.name)
                return None
                
        except Exception as e:
            print(f"❌ TTS合成异常: {e}")
            return None
    
    def play_audio(self, audio_file: str):
        """播放音频文件"""
        if not self.audio_available:
            return
        
        try:
            # 停止当前播放
            if self.is_playing:
                pygame.mixer.music.stop()
            
            # 播放新音频
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
            self.is_playing = True
            
            # 等待播放完成
            while pygame.mixer.music.get_busy() and not self.stop_playback:
                time.sleep(0.1)
            
            self.is_playing = False
            
            # 清理临时文件
            try:
                os.unlink(audio_file)
            except:
                pass
                
        except Exception as e:
            print(f"❌ 音频播放失败: {e}")
            self.is_playing = False
    
    def speak_text(self, text: str):
        """文本转语音并播放"""
        if not self.enabled:
            return
        
        # 在新线程中处理TTS
        def tts_worker():
            audio_file = self.synthesize_text(text)
            if audio_file:
                self.play_audio(audio_file)
        
        thread = threading.Thread(target=tts_worker, daemon=True)
        thread.start()
    
    def stop_speaking(self):
        """停止当前播放"""
        self.stop_playback = True
        if self.is_playing:
            pygame.mixer.music.stop()
            self.is_playing = False
    
    def get_available_voices(self) -> list:
        """获取可用的中文女声列表"""
        return [
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
    
    def is_available(self) -> bool:
        """检查TTS是否可用"""
        return self.enabled and AZURE_AVAILABLE and self.audio_available
    
    def cleanup(self):
        """清理资源"""
        self.stop_speaking()
        try:
            pygame.mixer.quit()
        except:
            pass
