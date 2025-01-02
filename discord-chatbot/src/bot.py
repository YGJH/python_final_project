import discord
import json
import asyncio
from discord.ext import commands
from llm_jable_master import get_ollama_response
from gtts import gTTS
import os
import pygame
import speech_recognition as sr


def text_to_speech(text):
    tts = gTTS(text=text, lang='zh-TW')
    tts.save("response.mp3")


# 初始化 Discord bot
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True  # 添加語音狀態意圖
client = commands.Bot(command_prefix='%', intents=intents)

# 讀取影片詳細資料
with open("video_tetails.json", "r", encoding="utf-8") as f:
    video_details_list = json.load(f)

# # 添加對 JSON 各欄位的描述
# json_description = (
#     "這是影片的詳細資料，每個影片包含以下欄位：\n"
#     "1. title: 影片標題，開頭的代號非常重要，題到標題時一定要一並提到\n"
#     "2. url: 影片連結\n"
#     "3. models: 參與女優，很重要，一定要介紹\n"
#     "5. comments: 影片的評論，在介紹時評論可以讓主人更了解劇情\n"
# )

# 添加對 JSON 各欄位的描述
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


@client.event
async def on_ready():
    print(f"目前登入身份 --> {client.user}")


@client.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send("已加入語音頻道！")
    else:
        await ctx.send("您需要先加入語音頻道！")


@client.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.guild.voice_client.disconnect()
        await ctx.send("已離開語音頻道！")
    else:
        await ctx.send("機器人不在任何語音頻道中！")


@client.command()
async def speak(ctx, *, text: str):
    if ctx.voice_client:
        # 使用 text_to_speech 將文字轉換為語音
        text_to_speech(text)

        # 播放語音
        ctx.voice_client.play(discord.FFmpegPCMAudio(
            "response.mp3"), after=lambda e: print(f"播放完成: {e}"))
        await ctx.send(f"正在播放: {text}")
    else:
        await ctx.send("機器人不在任何語音頻道中！")


async def speech_to_text():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("請開始說話...")
        audio = r.listen(source)
        print("錄音完成！")

    try:
        print("正在辨識語音...")
        user_input = r.recognize_google(audio, language='zh-TW')
        print(f"辨識結果: {user_input}")
        return user_input
    except Exception as e:
        print(f"辨識失敗: {e}")
        return ""


@client.command()
async def listen(ctx):
    user_input = await speech_to_text()
    await ctx.send(f"您說：{user_input}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith('%'):
        await client.process_commands(message)
    elif message.content.startswith('!'):
        if message.content.lower() in ['退出', '結束', '離開']:
            await message.channel.send("謝謝您的使用，再見！")
        else:
            # 優化 prompt，提供更好的上下文
            # prompt = (
            #     f"你是一個活潑的女僕，平時喜歡看一些劇情豐富的影片，並且樂於和主人分享這些影片的劇情。\n\n"
            #     f"根據以下的影片詳細資料回答主人的問題。\n\n"
            #     f"{json_description}\n\n"
            #     f"這是影片的詳細資料：\n{json.dumps(
            #         video_details_list, ensure_ascii=False, indent=2)}\n\n"
            #     f"請根據上述資料為主人提供最相關的回答。\n"
            #     f"主人的問題：{message.content[1:]}\n\n"
            #     f"時刻記住，要用活潑女僕的語氣，並且以「喵」作為結尾，如果話語中穿插一些性感的字眼，主人會非常開心愉悅。"
            # )
            prompt = message.content[1:]
            # print(prompt)
            # 設置輸入中狀態
            async with message.channel.typing():
                # 傳送使用者輸入給 Ollama 並獲取回應
                ollama_response = await asyncio.to_thread(get_ollama_response, prompt)
                # 僅顯示 Ollama 的回應
                await message.channel.send(f"Ollama 回應: {ollama_response}")

client.run(
    'TOKEN')
