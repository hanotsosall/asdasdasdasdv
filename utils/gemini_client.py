import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL

genai.configure(api_key=GEMINI_API_KEY)

def list_available_models():
    """Для отладки: вывести все доступные модели"""
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)

def ask_gemini_with_history(prompt: str, history: list) -> str:
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        chat = model.start_chat(history=[])
        
        # Добавляем историю (если нужна)
        for role, content in history:
            if role == 'user':
                chat.send_message(content)
            # Для ассистента в history не отправляем повторно, т.к. start_chat чистый
        response = chat.send_message(prompt)
        return response.text
    except Exception as e:
        # Если модель не найдена, выдать понятную ошибку
        if "not found" in str(e):
            return f"⚠️ Модель {GEMINI_MODEL} недоступна. Попробуй: gemini-1.5-pro, gemini-1.5-flash, gemini-pro. Проверь API ключ и регион."
        return f"⚠️ Ошибка Gemini: {e}"

def ask_gemini(prompt: str) -> str:
    return ask_gemini_with_history(prompt, [])
