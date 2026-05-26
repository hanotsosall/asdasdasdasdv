from aiogram import Router, types
from aiogram.filters import F
from aiogram.types import CallbackQuery
from database import get_user, update_user, clear_history
from keyboards import settings_menu, ai_choice_menu, image_model_menu, back_button

router = Router()

@router.callback_query(F.data == "settings")
async def settings_menu_handler(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    current_ai = user['default_ai']
    await callback.message.edit_text(
        "⚙️ **Настройки**\n\nВыбери, что изменить:",
        reply_markup=settings_menu(current_ai),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "change_default_ai")
async def change_default_ai_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "Выбери **основную ИИ**, которая будет отвечать по умолчанию:",
        reply_markup=ai_choice_menu(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("set_ai_"))
async def set_default_ai(callback: CallbackQuery):
    ai_name = callback.data.split("_")[-1]
    user_id = callback.from_user.id
    update_user(user_id, default_ai=ai_name)
    await callback.answer(f"✅ Основная ИИ изменена на {ai_name.upper()}")
    user = get_user(user_id)
    await callback.message.edit_text(
        "⚙️ **Настройки**\n\nВыбери, что изменить:",
        reply_markup=settings_menu(user['default_ai']),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "clear_history")
async def clear_history_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    clear_history(user_id)
    await callback.answer("🗑 История диалогов очищена", show_alert=True)
    user = get_user(user_id)
    await callback.message.edit_text(
        "⚙️ **Настройки**\n\nВыбери, что изменить:",
        reply_markup=settings_menu(user['default_ai']),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "image_model_settings")
async def image_model_settings(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    current_model = user.get('image_model', 'pollinations')
    await callback.message.edit_text(
        "Выбери модель для генерации изображений:",
        reply_markup=image_model_menu(current_model)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("set_image_model_"))
async def set_image_model(callback: CallbackQuery):
    model = callback.data.split("_")[-1]
    update_user(callback.from_user.id, image_model=model)
    await callback.answer(f"✅ Модель изображений: {model}")
    user = get_user(callback.from_user.id)
    await callback.message.edit_text(
        "⚙️ **Настройки**\n\nВыбери, что изменить:",
        reply_markup=settings_menu(user['default_ai']),
        parse_mode="Markdown"
    )
