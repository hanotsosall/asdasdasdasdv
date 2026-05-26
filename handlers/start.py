from aiogram import Router, types
from aiogram.filters import Command
from database import get_user, add_referral
from keyboards import main_menu
from config import ADMIN_ID
from keyboards import admin_panel

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref_"):
        ref_id = int(args[1].split("_")[1])
        if ref_id != user_id:
            add_referral(ref_id, user_id)
    user = get_user(user_id)
    text = (
        "🚀 **Ultimate AI Bot**\n\n"
        "Я объединяю **Groq (LLaMA 3)** и **DeepSeek** – две мощные нейросети.\n"
        "🎨 Генерирую изображения по тексту.\n\n"
        f"💎 У тебя осталось **{user['balance_requests']}** бесплатных запросов.\n"
        "➕ Приглашай друзей (+5 запросов за каждого).\n"
        "👇 Выбери действие:"
    )
    await message.answer(text, reply_markup=main_menu(), parse_mode="Markdown")

@router.message(Command("admin"))
async def admin_command(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("👑 Админ-панель", reply_markup=admin_panel())
    else:
        await message.answer("Нет доступа")
