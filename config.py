import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")   # новый ключ

# Модели по умолчанию
GROQ_MODEL = "llama-3.3-70b-versatile"   # актуальная
DEEPSEEK_MODEL = "deepseek-chat"
GEMINI_MODEL = "gemini-1.5-pro"
