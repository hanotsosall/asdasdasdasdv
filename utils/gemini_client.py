import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL

genai.configure(api_key=GEMINI_API_KEY)

def ask_gemini_with_history(prompt: str, history: list) -> str:
    """history: список пар (role, content), где role = 'user' или 'model'"""
    model = genai.GenerativeModel(GEMINI_MODEL)
    chat = model.start_chat(history=[])
    # Добавляем предыдущие сообщения
    for role, content in history:
        # В Gemini role: 'user' или 'model' (ассистент)
        if role == 'assistant':
            role = 'model'
        chat.history.append({"role": role, "parts": [content]})
    response = chat.send_message(prompt)
    return response.text

def ask_gemini(prompt: str) -> str:
    return ask_gemini_with_history(prompt, [])
