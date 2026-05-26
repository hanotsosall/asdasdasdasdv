import groq
from config import GROQ_API_KEY

import os

# Убираем прокси-переменные, чтобы httpx их не подхватил
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)

client = groq.Groq(api_key=GROQ_API_KEY)

def ask_groq(prompt: str) -> str:
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1024
    )
    return response.choices[0].message.content
