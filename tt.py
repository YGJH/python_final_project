import ollama

def test_ollama():
    prompt = "請推薦一部科幻電影。"
    try:
        chinese_prompt = f"請用中文回答：{prompt}"
        response = ollama.generate(prompt=chinese_prompt, model="llama3:8b")
        print(f"Ollama 回應: {response}")
    except Exception as e:
        print(f"錯誤: {e}")

if __name__ == "__main__":
    test_ollama()