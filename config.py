import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")   # вместо OPENAI_API_KEY

GROQ_MODEL = "mixtral-8x7b-32768"
GEMINI_MODEL = "gemini-1.5-flash"   # или "gemini-1.5-pro" (тоже бесплатно, но лимит ниже)
