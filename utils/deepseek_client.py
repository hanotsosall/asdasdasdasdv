import requests
from config import DEEPSEEK_API_KEY, DEEPSEEK_MODEL

def ask_deepseek_with_history(prompt: str, history: list) -> str:
    messages = []
    for role, content in history:
        messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": prompt})
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1024
    }
    response = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=data)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"⚠️ Ошибка DeepSeek: {response.text}"

def ask_deepseek(prompt: str) -> str:
    return ask_deepseek_with_history(prompt, [])
