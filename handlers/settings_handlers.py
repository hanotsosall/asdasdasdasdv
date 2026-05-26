from aiogram import Router, types, F
from database import get_user, update_user, clear_history
from keyboards import settings_menu, ai_choice_menu, image_model_menu, back_button

router = Router()

@router.callback_query(F.data == "settings")
async def settings_menu_handler(callback: types.CallbackQuery):
    user = get_user(callback.from_user.id)
    current_ai = user['default_ai']
    await callback.message.edit_text(
        "⚙️ **Настройки**\n\nВыбери, что изменить:",
        reply_markup=settings_menu(current_ai),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "change_default_ai")
async def change_default_ai_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "Выбери **основную ИИ**, которая будет отвечать по умолчанию:",
        reply_markup=ai_choice_menu(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("set_ai_"))
async def set_default_ai(callback: types.CallbackQuery):
    ai_name = callback.data.split("_")[-1]  # groq / deepseek / gemini
    user_id = callback.from_user.id
    update_user(user_id, default_ai=ai_name)
    await callback.answer(f"✅ Основная ИИ изменена на {ai_name.upper()}")
    # вернуться в настройки
    user = get_user(user_id)
    await callback.message.edit_text(
        "⚙️ **Настройки**\n\nВыбери, что изменить:",
        reply_markup=settings_menu(user['default_ai']),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "clear_history")
async def clear_history_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    clear_history(user_id)  # очистить всю историю
    await callback.answer("🗑 История диалогов очищена", show_alert=True)
    user = get_user(user_id)
    await callback.message.edit_text(
        "⚙️ **Настройки**\n\nВыбери, что изменить:",
        reply_markup=settings_menu(user['default_ai']),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "image_model_settings")
async def image_model_settings(callback: types.CallbackQuery):
    # по умолчанию храним выбор в базе? добавим поле image_model в users, но для простоты используем глобальную переменную или отдельную таблицу.
    # Сделаем отдельную таблицу user_settings.
    # Но для скорости: добавим поле image_model в таблицу users (создадим миграцию)
    # Обновим database.py позже. Сейчас просто заглушка, чтобы не ломать.
    # Временно храним в памяти или в users.
    # Для полноты: добавим поле в database.py:
    # ALTER TABLE users ADD COLUMN image_model TEXT DEFAULT 'pollinations'
    # Но чтобы не переписывать, сделаем через get_user/update_user с новым полем.
    # Я добавлю это поле в database.py ниже. Пока что просто вызовем меню.
    user = get_user(callback.from_user.id)
    current_model = user.get('image_model', 'pollinations')
    await callback.message.edit_text(
        "Выбери модель для генерации изображений:",
        reply_markup=image_model_menu(current_model)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("set_image_model_"))
async def set_image_model(callback: types.CallbackQuery):
    model = callback.data.split("_")[-1]  # pollinations или nano_banana
    # сохраним в пользователе
    update_user(callback.from_user.id, image_model=model)
    await callback.answer(f"✅ Модель изображений: {model}")
    # вернуться в меню настроек
    user = get_user(callback.from_user.id)
    await callback.message.edit_text(
        "⚙️ **Настройки**\n\nВыбери, что изменить:",
        reply_markup=settings_menu(user['default_ai']),
        parse_mode="Markdown"
    )
