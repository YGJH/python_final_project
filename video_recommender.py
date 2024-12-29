import json
import random
import ollama
import speech_recognition as sr
from gtts import gTTS
import os
import pygame
import threading
from queue import Queue
import time
import sys
import itertools

# 初始化 pygame
pygame.mixer.init()

# 動畫效果
done = False
def animate():
    for c in itertools.cycle(['|', '/', '-', '\\']):
        if done:
            break
        sys.stdout.write('\r思考中 ' + c)
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write('\r完成!     \n')

class SpeechToText:
    def __init__(self):
        self.recognizer = self.optimize_speech_recognition()
        self.audio_queue = Queue()
        threading.Thread(target=self.process_audio, daemon=True).start()

    def optimize_speech_recognition(self):
        r = sr.Recognizer()
        r.energy_threshold = 300  # 降低能量閾值，提高靈敏度
        r.dynamic_energy_threshold = True  # 動態調整能量閾值
        r.pause_threshold = 190  # 縮短暫停時間
        r.non_speaking_duration = 190  # 縮短非說話時間
        return r

    def process_audio(self):
        with sr.Microphone() as source:
            print("開始聆聽...")
            while True:
                try:
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                    self.audio_queue.put(audio)
                except sr.WaitTimeoutError:
                    continue

    def listen(self):
        if not self.audio_queue.empty():
            audio = self.audio_queue.get()
            try:
                text = self.recognizer.recognize_google(audio, language='zh-TW')
                print(f"您說：{text}")
                return text
            except sr.UnknownValueError:
                print("抱歉，我無法理解您說的內容。")
            except sr.RequestError:
                print("無法連接語音服務。")
        return ''

    def __call__(self):
        return self.listen()

def text_to_speech(text):
    tts = gTTS(text=text, lang='zh', slow=False)
    tts.save("response.mp3")
    pygame.mixer.music.load("response.mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    pygame.mixer.music.unload()
    os.remove("response.mp3")

class VideoRecommender:
    def __init__(self):
        self.video_data = self.load_video_data()
        self.speech_to_text = SpeechToText()
        
    def load_video_data(self):
        with open('video_details.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_random_videos(self, n=3):
        """隨機獲取n個影片作為上下文"""
        return random.sample(self.video_data, min(n, len(self.video_data)))
    
    def create_prompt(self, user_preferences=None):
        """創建推薦提示"""
        context_videos = self.get_random_videos()
        
        prompt = "你是一個專業的影片推薦助手。請用繁體中文回答以下問題。根據以下影片資訊，推薦一部適合的影片：\n\n"
        
        # 添加上下文影片
        for i, video in enumerate(context_videos, 1):
            prompt += f"影片 {i}:\n"
            prompt += f"標題: {video['title']}\n"
            if video['models']:
                prompt += f"演員: {', '.join(video['models'])}\n"
            if video['comments']:
                prompt += f"評論: {' | '.join(video['comments'][:3])}\n"
            prompt += "\n"
        
        if user_preferences:
            prompt += f"使用者偏好: {user_preferences}\n\n"
        
        prompt += "請用繁體中文回答以下問題：\n1. 推薦一部最適合的影片\n2. 說明為什麼推薦這部影片\n請控制回答在100字以內。"
        return prompt
    
    def recommend(self, user_preferences=None):
        """生成推薦"""
        global done
        done = False
        t = threading.Thread(target=animate)
        t.start()

        prompt = self.create_prompt(user_preferences)
        
        try:
            response = ollama.chat(model='llama2', messages=[
                {
                    'role': 'system',
                    'content': '你是一個專業的影片推薦助手。請務必使用繁體中文回答所有問題。'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ])
            recommendation = response['message']['content']
            done = True
            t.join()
            
            # 使用語音輸出推薦結果
            print("\n" + recommendation + "\n")
            text_to_speech(recommendation)
            
            return recommendation
        except Exception as e:
            done = True
            t.join()
            error_msg = f"推薦生成失敗: {str(e)}"
            print("\n" + error_msg + "\n")
            text_to_speech(error_msg)
            return error_msg

def main():
    recommender = VideoRecommender()
    print("歡迎使用影片推薦系統！")
    text_to_speech("歡迎使用影片推薦系統！請說出您的偏好，或是直接說「推薦」來獲取一般推薦。")
    
    while True:
        print("\n請說出您的偏好，或是直接說「推薦」來獲取一般推薦（說「退出」來結束程式）：")
        user_input = recommender.speech_to_text()
        
        if not user_input:
            continue
            
        if user_input in ["退出", "結束", "離開"]:
            text_to_speech("感謝使用，再見！")
            break
            
        if user_input == "推薦":
            recommender.recommend()
        else:
            recommender.recommend(user_input)

if __name__ == "__main__":
    main()
