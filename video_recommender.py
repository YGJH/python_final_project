import json
import random
import sys
import time
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QPushButton, QTextEdit, QLabel, QMessageBox, QLineEdit, QHBoxLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from gtts import gTTS
import pygame
import ollama
from transformers import (
    AutoModelForCausalLM, 
    AutoTokenizer,
    BitsAndBytesConfig  # 添加這行
)
from peft import PeftModel
import torch
import speech_recognition as sr
from ollama import Client

# 初始化 pygame
pygame.mixer.init()

class SpeechThread(QThread):
    """語音識別執行緒"""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def run(self):
        try:
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                audio = recognizer.listen(source, timeout=5)
            text = recognizer.recognize_google(audio, language='zh-TW')
            self.finished.emit(text)
        except Exception as e:
            self.error.emit(str(e))

class TextToSpeechThread(QThread):
    """文字轉語音執行緒"""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, text):
        super().__init__()
        self.text = text
        self.is_playing = False
        
    def run(self):
        try:
            # 生成語音檔案
            tts = gTTS(text=self.text, lang='zh-tw')
            temp_file = 'temp_speech.mp3'
            
            # 刪除舊的臨時文件
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            # 保存新的語音文件
            tts.save(temp_file)
            
            # 播放語音
            self.is_playing = True
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            
            # 等待播放完成或被中斷
            while pygame.mixer.music.get_busy() and self.is_playing:
                pygame.time.Clock().tick(10)
            
            # 清理
            pygame.mixer.music.stop()
            pygame.mixer.quit()
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            self.finished.emit()
            
        except Exception as e:
            self.error.emit(str(e))
    
    def stop(self):
        """停止播放"""
        self.is_playing = False
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()

class RecommenderThread(QThread):
    """推薦生成執行緒"""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, recommender, preference=None):
        super().__init__()
        self.recommender = recommender
        self.preference = preference
        self.is_running = False
        
    def run(self):
        try:
            self.is_running = True
            print(self.preference)
            result = self.recommender.generate_recommendation(self.preference)
            print('result:', result)
            if self.is_running:  # 只有在沒有被中斷的情況下才發送結果
                self.finished.emit(result)
        except Exception as e:
            if self.is_running:
                self.error.emit(str(e))
    
    def stop(self):
        """停止推薦生成"""
        self.is_running = False

class VideoRecommender:
    def __init__(self):
        """初始化 Ollama llama3 模型"""
        print("初始化客戶端...")
        try:
            self.client = Client(host='http://localhost:11434')
            # 測試連線
            response = self.client.chat(
                model='Meta-Llama-3.1-8B-Instruct-abliterated:latest',
                messages=[{'role': 'user', 'content': 'test'}]
            )
            print("模型載入成功")
            return None
        except Exception as e:
            print(f"模型初始化失敗: {e}")
            return None
            
    def generate_recommendation(self, text):
        """根據影片資訊生成推薦理由"""
        try:
            # 構建提示詞
            prompt = f"""幫我在以下影片資訊裏頭，找出符合使用者偏好的影片: \"{text}\"
                    """
            with open ('video_details.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                for video in data:
                    prompt += f"""
                    video_url: {video['url']}
                    標題: {video['title']}
                    觀看次數: {video['views']}
                    評分: {video['rating']}
                    models: {', '.join(video['models'])}
                    tags: {', '.join(video['tags'])}
                """
            prompt += '請記得要用中文回答我。'
            print(prompt)
            # 呼叫 Ollama API
            start_time = time.time()

            response = self.client.chat(
                model='llama3:8b',
                messages=[
                    {'role' : 'system', 'content': '你是一個專業的影片推薦助手，根據以下的影片資訊回答使用者的問題。'},
                    {'role': 'user', 'content': prompt}
                    ]
            )
            elapsed_time = time.time() - start_time
            while elapsed_time < 15:
                start_time = time.time()
                response = self.client.chat(
                    model='Meta-Llama-3.1-8B-Instruct-abliterated:latest',
                    messages=[
                        {'role' : 'system', 'content': '你是一個專業的影片推薦助手，根據以下的影片資訊回答使用者的問題。'},
                        {'role': 'user', 'content': prompt}
                        ]
                )
                elapsed_time = time.time() - start_time
            print(response)
            return response['message']['content']
        except Exception as e:
            print(f"生成推薦失敗: {e}")
            return "無法生成推薦內容"

class VideoRecommenderGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.recommender = VideoRecommender()
        self.speech_thread = None
        self.tts_thread = None
        self.recommender_thread = None
        self.init_ui()
        
    def init_ui(self):
        """初始化使用者界面"""
        self.setWindowTitle('影片推薦系統')
        self.setGeometry(100, 100, 800, 600)
        
        # 創建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 創建輸入區域
        input_layout = QHBoxLayout()
        self.input_text = QLineEdit()
        self.input_text.setPlaceholderText('請輸入您的偏好...')
        input_layout.addWidget(self.input_text)
        
        # 語音輸入按鈕
        self.voice_button = QPushButton('🎤 語音輸入')
        self.voice_button.clicked.connect(self.start_voice_input)
        input_layout.addWidget(self.voice_button)
        
        # 搜尋按鈕
        self.search_button = QPushButton('🔍 搜尋')
        self.search_button.clicked.connect(self.start_search)
        input_layout.addWidget(self.search_button)
        
        layout.addLayout(input_layout)
        
        # 狀態標籤
        self.status_label = QLabel('')
        layout.addWidget(self.status_label)
        
        # 結果顯示區域
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        layout.addWidget(self.result_text)
        
        # 控制按鈕區域
        control_layout = QHBoxLayout()
        
        # 停止搜尋按鈕
        self.stop_search_button = QPushButton('⏹ 停止搜尋')
        self.stop_search_button.clicked.connect(self.stop_search)
        self.stop_search_button.setEnabled(False)
        control_layout.addWidget(self.stop_search_button)
        
        # 語音播放按鈕
        self.speak_button = QPushButton('🔊 播放')
        self.speak_button.clicked.connect(self.start_speech)
        self.speak_button.setEnabled(False)
        control_layout.addWidget(self.speak_button)
        
        # 停止播放按鈕
        self.stop_speak_button = QPushButton('🔇 停止播放')
        self.stop_speak_button.clicked.connect(self.stop_speech)
        self.stop_speak_button.setEnabled(False)
        control_layout.addWidget(self.stop_speak_button)
        
        layout.addLayout(control_layout)
        
        # 設置樣式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1E1E1E;
            }
            QWidget {
                color: white;
                font-size: 14px;
            }
            QLineEdit {
                padding: 8px;
                background-color: #2E2E2E;
                border: 1px solid #3E3E3E;
                border-radius: 4px;
                color: white;
            }
            QPushButton {
                padding: 8px 16px;
                background-color: #0D47A1;
                border: none;
                border-radius: 4px;
                color: white;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
            QPushButton:disabled {
                background-color: #424242;
            }
            QTextEdit {
                background-color: #2E2E2E;
                border: 1px solid #3E3E3E;
                border-radius: 4px;
                color: white;
                padding: 8px;
            }
            QLabel {
                color: #E0E0E0;
            }
        """)
    
    def start_voice_input(self):
        """開始語音輸入"""
        try:
            self.voice_button.setEnabled(False)
            self.voice_button.setText('🎤 正在聆聽...')
            self.status_label.setText('正在聆聽您的語音...')
            
            self.speech_thread = SpeechThread()
            self.speech_thread.finished.connect(self.handle_speech_result)
            self.speech_thread.error.connect(self.handle_speech_error)
            self.speech_thread.start()
            
        except Exception as e:
            self.handle_speech_error(str(e))
    
    def handle_speech_result(self, text):
        """處理語音識別結果"""
        self.input_text.setText(text)
        self.status_label.setText('語音識別完成')
        self.voice_button.setText('🎤 語音輸入')
        self.voice_button.setEnabled(True)
    
    def handle_speech_error(self, error):
        """處理語音識別錯誤"""
        self.status_label.setText(f'語音識別錯誤：{error}')
        self.voice_button.setText('🎤 語音輸入')
        self.voice_button.setEnabled(True)
    
    def start_search(self):
        """開始搜尋推薦"""
        preference = self.input_text.text().strip()
        if not preference:
            QMessageBox.warning(self, '提示', '請先輸入偏好')
            return
        
        self.status_label.setText('正在生成推薦...')
        self.search_button.setEnabled(False)
        self.stop_search_button.setEnabled(True)
        self.speak_button.setEnabled(False)
        
        self.recommender_thread = RecommenderThread(self.recommender, preference)
        self.recommender_thread.finished.connect(self.handle_search_result)
        self.recommender_thread.error.connect(self.handle_search_error)
        self.recommender_thread.start()
    
    def stop_search(self):
        """停止搜尋"""
        if self.recommender_thread and self.recommender_thread.is_running:
            self.recommender_thread.stop()
            self.status_label.setText('搜尋已停止')
            self.search_button.setEnabled(True)
            self.stop_search_button.setEnabled(False)
    
    def handle_search_result(self, result):
        """處理搜尋結果"""
        self.result_text.setText(result)
        self.status_label.setText('推薦完成')
        self.search_button.setEnabled(True)
        self.stop_search_button.setEnabled(False)
        self.speak_button.setEnabled(True)
    
    def handle_search_error(self, error):
        """處理搜尋錯誤"""
        self.status_label.setText(f'推薦生成錯誤：{error}')
        self.search_button.setEnabled(True)
        self.stop_search_button.setEnabled(False)
    
    def start_speech(self):
        """開始語音播放"""
        text = self.result_text.toPlainText()
        if not text:
            return
        
        self.speak_button.setEnabled(False)
        self.stop_speak_button.setEnabled(True)
        self.status_label.setText('正在播放...')
        
        self.tts_thread = TextToSpeechThread(text)
        self.tts_thread.finished.connect(self.handle_speech_finished)
        self.tts_thread.error.connect(self.handle_tts_error)
        self.tts_thread.start()
    
    def stop_speech(self):
        """停止語音播放"""
        if self.tts_thread and self.tts_thread.is_playing:
            self.tts_thread.stop()
            self.status_label.setText('播放已停止')
            self.speak_button.setEnabled(True)
            self.stop_speak_button.setEnabled(False)
    
    def handle_speech_finished(self):
        """處理語音播放完成"""
        self.status_label.setText('播放完成')
        self.speak_button.setEnabled(True)
        self.stop_speak_button.setEnabled(False)
    
    def handle_tts_error(self, error):
        """處理語音播放錯誤"""
        self.status_label.setText(f'語音播放錯誤：{error}')
        self.speak_button.setEnabled(True)
        self.stop_speak_button.setEnabled(False)

def main():
    app = QApplication(sys.argv)
    gui = VideoRecommenderGUI()
    gui.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
