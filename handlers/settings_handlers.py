from aiogram import Router
from aiogram.types import CallbackQuery
from database import get_user, update_user, clear_history
from keyboards import settings_menu, ai_choice_menu, back_button

router = Router()

@router.callback_query(lambda c: c.data == "settings")
async def settings_menu_handler(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    current_ai = user['default_ai']
    await callback.message.edit_text(
        "⚙️ <b>Настройки</b>\n\nВыбери, что изменить:",
        reply_markup=settings_menu(current_ai),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(lambda c: c.data == "change_default_ai")
async def change_default_ai_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "Выбери <b>основную ИИ</b>, которая будет отвечать по умолчанию:",
        reply_markup=ai_choice_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("set_ai_"))
async def set_default_ai(callback: CallbackQuery):
    ai_name = callback.data.split("_")[-1]  # groq, gemini или neurohama
    user_id = callback.from_user.id
    update_user(user_id, default_ai=ai_name)
    await callback.answer(f"✅ Основная ИИ изменена на {ai_name.upper()}")
    user = get_user(user_id)
    await callback.message.edit_text(
        "⚙️ <b>Настройки</b>\n\nВыбери, что изменить:",
        reply_markup=settings_menu(user['default_ai']),
        parse_mode="HTML"
    )

@router.callback_query(lambda c: c.data == "clear_history")
async def clear_history_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    clear_history(user_id)
    await callback.answer("🗑 История диалогов очищена", show_alert=True)
    user = get_user(user_id)
    await callback.message.edit_text(
        "⚙️ <b>Настройки</b>\n\nВыбери, что изменить:",
        reply_markup=settings_menu(user['default_ai']),
        parse_mode="HTML"
    )
