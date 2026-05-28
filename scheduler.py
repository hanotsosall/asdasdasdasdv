from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from database import daily_job

scheduler = AsyncIOScheduler()

def start_scheduler():
    # Запускаем каждый день в 00:00 UTC (можно поменять часовой пояс)
    scheduler.add_job(daily_job, CronTrigger(hour=0, minute=0))
    scheduler.start()
    print("⏰ Планировщик ежедневных задач запущен (каждый день в 00:00 UTC)")
