import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database import init_db
from handlers.start import router as start_router
from handlers.ai_handlers import router as ai_router
from handlers.image_handlers import router as image_router
from handlers.profile_handlers import router as profile_router
from handlers.referral_handlers import router as referral_router
from handlers.payment_handlers import router as payment_router
from handlers.admin_handlers import router as admin_router
from handlers.settings_handlers import router as settings_router   # новый
from handlers.message_handler import router as message_router       # для основной ИИ

async def main():
    init_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(start_router)
    dp.include_router(ai_router)         # обработка кнопок Groq/DeepSeek/Gemini (сохраняется)
    dp.include_router(image_router)
    dp.include_router(profile_router)
    dp.include_router(referral_router)
    dp.include_router(payment_router)
    dp.include_router(admin_router)
    dp.include_router(settings_router)   # настройки
    dp.include_router(message_router)    # обработка обычных сообщений (основная ИИ)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
