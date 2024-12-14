import speech_recognition as sr
import pyttsx3
import ollama

# Initialize the recognizer 
class SpeechToText:
    def __init__(self):  
        self.rg = sr.Recognizer()
        
    def listen(self):  
        with sr.Microphone() as source:
            print("請開始說話...")
            self.rg.adjust_for_ambient_noise(source, duration=0.2)  
            try:
                audioData = self.rg.listen(source, timeout=5, phrase_time_limit=10)
                text = self.rg.recognize_google(audioData, language='zh-tw') 
                # 移除使用者輸入的打印
                # print(f"您說: {text}")
            except sr.WaitTimeoutError:
                text = ''
                # 移除聆聽超時的打印
                # print("聆聽超時，請再試一次。")
            except sr.UnknownValueError:
                text = ''
                # 移除無法理解語音的打印
                # print("抱歉，我無法理解您說的內容。")
            except sr.RequestError:
                text = ''
                # 移除無法連接語音服務的打印
                # print("無法連接語音服務。")
        return text
    
    def __call__(self):
        return self.listen()    

# Convert text to speech
def text_to_speech(command):
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    # 選擇中文語音
    for voice in voices:
        try:
            if 'zh' in voice.languages[0]:
                engine.setProperty('voice', voice.id)
                break
        except (AttributeError, IndexError):
            continue
    engine.setProperty('rate', 150)  # 語速
    engine.setProperty('volume', 1.0)  # 音量
    engine.say(command) 
    engine.runAndWait()

# 獲取 Ollama 回應
def get_ollama_response(prompt):
    try:
        # 在提示前添加指示，請求中文回應
        chinese_prompt = f"請用中文回答：{prompt}"
        response = ollama.generate(prompt=chinese_prompt, model="llama3:8b")
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