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
        self.recognizer = sr.Recognizer()

    def listen(self):
        with sr.Microphone() as source:
            print("請說話...")
            audio = self.recognizer.listen(source)
            try:
                text = self.recognizer.recognize_google(
                    audio, language='zh-TW')
                print(f"您說：{text}")
            except sr.UnknownValueError:
                text = ''
                print("抱歉，我無法理解您說的內容。")
            except sr.RequestError:
                text = ''
                print("無法連接語音服務。")
        return text

    def __call__(self):
        return self.listen()

# 文字轉語音


def text_to_speech(command):
    tts = gTTS(text=command, lang='zh')
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
        chinese_prompt = f"請用中文回答：{prompt}，不超過20字"
        response = ollama.generate(
            prompt=chinese_prompt, model="adsfaaron/taide-lx-7b-chat:q5")
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
    while True:
        user_input = speech_to_text()
        if user_input.lower() in ['退出', '結束', '離開']:
            text_to_speech("謝謝您的使用，再見！")
            break
        elif user_input:
            # 傳送使用者輸入給 Ollama 並獲取回應
            ollama_response = get_ollama_response(user_input)
            # 僅顯示 Ollama 的回應
            print(f"Ollama 回應: {ollama_response}")
            # 將 Ollama 的回應轉換為語音
            text_to_speech(ollama_response)


if __name__ == "__main__":
    chatbot()
