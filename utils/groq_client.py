import os
for key in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
    os.environ.pop(key, None)

import httpx
import groq
from config import GROQ_API_KEY, GROQ_MODEL

http_client = httpx.Client()
client = groq.Groq(api_key=GROQ_API_KEY, http_client=http_client)

def ask_groq_with_history(prompt: str, history: list) -> str:
    """
    history: список кортежей (role, content), где role = 'user' или 'assistant'
    """
    messages = []
    for role, content in history:
        messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": prompt})
    
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=1024
    )
    return response.choices[0].message.content

# Старая функция для обратной совместимости (если нужна без истории)
def ask_groq(prompt: str) -> str:
    return ask_groq_with_history(prompt, [])
