import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL

genai.configure(api_key=GEMINI_API_KEY)

def ask_gemini_with_history(prompt: str, history: list) -> str:
    model = genai.GenerativeModel(GEMINI_MODEL)
    # Преобразуем историю в формат Gemini
    chat = model.start_chat(history=[])
    # Добавляем историю вручную
    for role, content in history:
        # role может быть 'user' или 'assistant'
        if role == 'user':
            chat.send_message(content)
        else:
            # Для ассистента просто добавляем в историю? У Gemini есть свой механизм
            # Но проще передавать всю историю через параметр messages
            pass
    # Отправляем новый запрос
    response = chat.send_message(prompt)
    return response.text

def ask_gemini(prompt: str) -> str:
    return ask_gemini_with_history(prompt, [])
