import os

# !!! Важно: удаляем прокси-переменные ДО импорта httpx и groq
for key in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
    os.environ.pop(key, None)

import httpx
import groq
from config import GROQ_API_KEY

# Создаём чистый http-клиент (переменные уже отсутствуют)
http_client = httpx.Client()

client = groq.Groq(
    api_key=GROQ_API_KEY,
    http_client=http_client
)

def ask_groq(prompt: str) -> str:
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1024
    )
    return response.choices[0].message.content
