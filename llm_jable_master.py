import json
import random
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import sounddevice as sd
import numpy as np
import speech_recognition as sr
from gtts import gTTS
import os
import pygame
import ollama
import itertools
import threading
import time
import sys
from queue import Queue

# 初始化 pygame
pygame.mixer.init()

# 小動畫


def animate():
    for c in itertools.cycle(['|', '/', '-', '\\']):
        if done:
            break
        sys.stdout.write('\r思考中 ' + c)
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write('\r完成!     \n')

# 語音轉文字


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

# 文字轉語音


def text_to_speech(command):
    tts = gTTS(text=command, lang='zh', slow=False)  # 設定 slow=False 來加快語速
    tts.save("response.mp3")
    pygame.mixer.music.load("response.mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    pygame.mixer.music.unload()  # 確保音頻文件已經完全卸載
    os.remove("response.mp3")

# 獲取 Ollama 回應


def get_ollama_response(prompt):
    global done
    done = False
    t = threading.Thread(target=animate)
    t.start()
    try:
        # 在提示前添加指示，請求中文回應
        chinese_prompt = f"請用只用中文回答：{prompt}，不超過80字"
        response = ollama.generate(
            prompt=chinese_prompt, model="llama3:8b")
        # 檢查回應類型並返回 'response' 屬性
        if hasattr(response, 'response') and isinstance(response.response, str):
            return response.response
        elif isinstance(response, str):
            return response
        else:
            return "抱歉，我無法獲取回應。"
    except Exception as e:
        print(f"Ollama 回應錯誤: {e}")
        return "抱歉，我無法獲取回應。"
    finally:
        done = True
        t.join()

# 主聊天機器人功能


def chatbot():
    speech_to_text = SpeechToText()
    with open("video_detailss.json", "r", encoding="utf-8") as f:
        video_details_list = json.load(f)

    # 添加對 JSON 各欄位的描述
    json_description = (
        "這是影片的詳細資料，每個影片包含以下欄位：\n"
        "1. title: 影片標題\n"
        "2. description: 影片描述\n"
        "3. genre: 影片類型\n"
        "4. actors: 參與演員\n"
        "5. release_date: 發行日期\n"
        "6. rating: 評分\n"
    )

    while True:
        user_input = speech_to_text()
        flag = False
        for i in ['退出', '結束', '離開']:
            if i in user_input.lower():
                text_to_speech("謝謝您的使用，再見！")
                flag = True
                break
        if flag:
            break
        elif user_input:
            # 優化 prompt，提供更好的上下文
            prompt = (
                f"你是一個專業的影片推薦助手，根據以下的影片詳細資料回答使用者的問題。\n\n"
                f"{json_description}\n\n"
                f"這是影片的詳細資料：\n{json.dumps(video_details_list, ensure_ascii=False, indent=2)}\n\n"
                f"請根據上述資料提供最相關的回答。"
                f"使用者問題：{user_input}\n\n"
            )
            # 傳送使用者輸入給 Ollama 並獲取回應
            print(prompt)
            ollama_response = get_ollama_response(prompt)
            # 僅顯示 Ollama 的回應
            print(f"Ollama 回應: {ollama_response}")
            # 將 Ollama 的回應轉換為語音
            text_to_speech(ollama_response)


if __name__ == "__main__":
    chatbot()
