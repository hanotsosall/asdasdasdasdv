from aiogram import Router, types
from aiogram.filters import Command, Text
from aiogram.types import CallbackQuery
from database import get_user, add_referral
from keyboards import main_menu

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
    await message.answer(text, reply_markup=main_menu(user_id), parse_mode="Markdown")

@router.callback_query(Text("main_menu"))
async def back_to_main_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = get_user(user_id)
    text = (
        "🚀 **Ultimate AI Bot**\n\n"
        "Я объединяю **Groq (LLaMA 3)** и **DeepSeek** – две мощные нейросети.\n"
        "🎨 Генерирую изображения по тексту.\n\n"
        f"💎 У тебя осталось **{user['balance_requests']}** бесплатных запросов.\n"
        "➕ Приглашай друзей (+5 запросов за каждого).\n"
        "👇 Выбери действие:"
    )
    await callback.message.edit_text(text, reply_markup=main_menu(user_id), parse_mode="Markdown")
    await callback.answer()
