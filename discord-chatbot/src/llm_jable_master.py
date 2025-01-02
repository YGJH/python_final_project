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


def retrieve_relevant_documents(prompt):
    # 讀取 video_details.json 文件
    with open("video_tetails.json", "r", encoding="utf-8") as f:
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


def get_ollama_response(prompt):
    global done
    done = False
    t = threading.Thread(target=animate)
    t.start()
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
            ollama_response = get_ollama_response(user_input)
            print(f"Ollama 回應: {ollama_response}")
            text_to_speech(ollama_response)


if __name__ == "__main__":
    chatbot()
