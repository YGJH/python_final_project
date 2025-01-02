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
json_description = (
    "這是影片的詳細資料，每個影片包含以下欄位：\n"
    "1. score: 影片評分，可以當作影片的質量參考\n"
    "2. description: 影片描述，可以用來向主人介紹劇情\n"
    "3. url: 影片連結，可以讓主人直接觀看\n"
    "4. countryOfOrigin: 影片來源國家，可以讓主人了解影片的風格\n"
    "5. datePublished: 影片發布日期，可以讓主人了解影片的新舊\n"
    "6. image: 影片封面圖片，可以讓主人直觀了解影片內容\n"
    "7. director: 導演，可以讓主人了解影片的風格\n"
    "8. genre: 類型，可以讓主人了解影片的風格\n"
    "9. actors: 演員，可以讓主人了解影片的演出陣容\n"
    "10. name: 影片名稱，可以讓主人了解影片的名稱\n"
)
def retrieve_relevant_documents(prompt):
    # 讀取 video_details.json 文件
    with open("movies_details_modified.json", "r", encoding="utf-8") as f:
        video_details_list = json.load(f)

    # 檢索邏輯：根據提示檢索相關的影片
    relevant_docs = []
    for video in video_details_list:
        title = video.get('name')
        description = video.get('description')
        genre = video.get('genre')
        actors = video.get('actors')

        for actor in actors:
            if actor in prompt:
                relevant_docs.append(video)
                break

        for keyword in [title, description, genre]:
            if keyword and prompt in keyword:
                relevant_docs.append(video)
                break

    # 如果沒有找到相關的影片，回傳一個字串
    if not relevant_docs:
        return "詳細資料是空的，請用可愛的語氣告訴主人，找不到相關的影片"
    return relevant_docs


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
                model='EntropyYue/chatglm3:6b',
                messages=[{'role': 'user', 'content': 'test'}]
            )
            print("模型載入成功")
            return None
        except Exception as e:
            print(f"模型初始化失敗: {e}")
            return None
            
    def generate_recommendation(self, prompt):
        try:
            # 檢索相關文件
            relevant_docs = retrieve_relevant_documents(prompt)
            context = json.dumps(relevant_docs, ensure_ascii=False, indent=2)

            # 在提示前添加指示，請求中文回應
            # chinese_prompt = (
            #     f"你是一個專業的影片推薦助手，根據以下的影片詳細資料回答使用者的問題。\n\n"
            #     f"使用者問題：{prompt}\n\n"
            #     f"這是相關的影片詳細資料：\n{context}\n\n"
            #     f"請根據上述資料提供最相關的回答。"
            # )
            chinese_prompt = (
                f"你是一個活潑的女僕，平時喜歡看一些劇情豐富的影片，並且樂於和主人分享這些影片的劇情。\n\n"
                f"根據以下的影片詳細資料回答主人的問題。\n\n"
                f"{json_description}\n\n"
                f"這是影片的詳細資料：\n{context}\n\n"
                f"請根據上述資料為主人提供最相關的回答。\n"
                f"主人的問題：{prompt}\n\n"
                f"時刻記住，要用活潑女僕的語氣，並且以「喵」作為結尾，如果話語中穿插一些性感的字眼，主人會非常開心愉悅。\n\n"
                f"介紹影片時，一定要提到影片的名稱，並且介紹影片的演員，這樣主人才能更好地了解影片的內容。\n\n"
                f"(如果詳細資料是空的, 請用可愛的語氣告訴主人，找不到相關的影片喵。)"
            )
            response = ollama.generate(
                prompt=chinese_prompt, model="EntropyYue/chatglm3:6b")
            # 檢查回應類型並返回 'response' 屬性
            print(chinese_prompt)
            if hasattr(response, 'response') and isinstance(response.response, str):
                return response.response
            elif isinstance(response, str):
                return response
            else:
                return "抱歉，我無法獲取回應。"
        except Exception as e:
            print(f"Ollama 回應錯誤: {e}")
            return "抱歉，我無法獲取回應。"

# 主聊天機器人功能

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
