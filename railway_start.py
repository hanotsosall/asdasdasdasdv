import asyncio
import os
import uvicorn
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database import init_db, ensure_default_channel
from handlers.start import router as start_router
from handlers.ai_handlers import router as ai_router
from handlers.image_handlers import router as image_router
from handlers.profile_handlers import router as profile_router
from handlers.referral_handlers import router as referral_router
from handlers.payment_handlers import router as payment_router
from handlers.admin_handlers import router as admin_router
from handlers.settings_handlers import router as settings_router
from handlers.message_handler import router as message_router
from handlers.middlewares import SubscriptionMiddleware
from scheduler import start_scheduler
import webapp_server

async def run_bot():
    init_db()
    # Создаём папку для бэкапов, если её нет
    if not os.path.exists("backups"):
        os.makedirs("backups")
    bot = Bot(token=BOT_TOKEN)
    # Добавляем канал @UltimateAI_info в обязательные (если ещё не добавлен)
    await ensure_default_channel(bot, "UltimateAI_info")
    dp = Dispatcher()
    dp.message.middleware(SubscriptionMiddleware())
    dp.callback_query.middleware(SubscriptionMiddleware())
    dp.include_router(start_router)
    dp.include_router(ai_router)
    dp.include_router(image_router)
    dp.include_router(profile_router)
    dp.include_router(referral_router)
    dp.include_router(payment_router)
    dp.include_router(admin_router)
    dp.include_router(settings_router)
    dp.include_router(message_router)
    await dp.start_polling(bot)

async def run_api():
    port = int(os.environ.get("PORT", 8000))
    config = uvicorn.Config(webapp_server.app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    # Запускаем планировщик
    start_scheduler()
    # Запускаем бота и API параллельно
    await asyncio.gather(run_bot(), run_api())

if __name__ == "__main__":
    asyncio.run(main())
