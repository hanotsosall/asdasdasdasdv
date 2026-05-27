from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID
from database import (get_user, update_user, get_all_users, count_users,
                      clear_history, get_history, add_required_channel,
                      remove_required_channel, get_required_channels)
import sqlite3
from keyboards import admin_panel, back_button, admin_user_list_menu, admin_user_profile_buttons

router = Router()

class AdminStates(StatesGroup):
    waiting_broadcast = State()
    waiting_balance_user_id = State()
    waiting_balance_amount = State()
    waiting_sub_user_id = State()
    waiting_sub_days = State()
    waiting_msg_user_id = State()
    waiting_msg_text = State()
    waiting_channel_id = State()
    waiting_channel_username = State()
    waiting_channel_link = State()

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

# ---------- Статистика ----------
@router.callback_query(lambda c: c.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    conn = sqlite3.connect("bot_database.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    users_count = c.fetchone()[0]
    c.execute("SELECT SUM(total_requests) FROM users")
    total_req = c.fetchone()[0] or 0
    c.execute("SELECT SUM(total_images) FROM users")
    total_img = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM users WHERE subscribed=1")
    subscribed_count = c.fetchone()[0]
    conn.close()
    text = (f"📊 **Статистика**\n👥 Пользователей: {users_count}\n"
            f"📨 Всего запросов: {total_req}\n🖼️ Всего изображений: {total_img}\n"
            f"⭐ Подписка активна у: {subscribed_count}")
    await callback.message.edit_text(text, reply_markup=back_button("admin_panel"), parse_mode="Markdown")
    await callback.answer()

# ---------- Список пользователей ----------
@router.callback_query(lambda c: c.data.startswith("admin_users"))
async def admin_users(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    if "page_" in callback.data:
        page = int(callback.data.split("_")[-1])
    else:
        page = 0
    limit = 5
    total = count_users()
    offset = page * limit
    users = get_all_users(limit, offset)
    total_pages = (total + limit - 1) // limit
    text = f"👥 **Пользователи** (стр. {page+1}/{total_pages}):\n"
    for u in users:
        text += f"🆔 {u['user_id']} | {u.get('username') or 'no name'} | Баланс: {u['balance_requests']} | Подписка: {'✅' if u['subscribed'] else '❌'}\n"
    await callback.message.edit_text(text, reply_markup=admin_user_list_menu(users, page, total_pages), parse_mode="Markdown")
    await callback.answer()

# ---------- Профиль пользователя из админки ----------
@router.callback_query(lambda c: c.data.startswith("admin_user_"))
async def admin_user_profile(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    target_id = int(callback.data.split("_")[-1])
    user = get_user(target_id)
    text = (
        f"👤 **Профиль пользователя**\n"
        f"🆔 ID: `{user['user_id']}`\n"
        f"👤 Username: @{user.get('username') or 'нет'}\n"
        f"💰 Баланс: {user['balance_requests']} запросов\n"
        f"⭐ Подписка: {'✅ Активна' if user['subscribed'] else '❌ Нет'}\n"
        f"📊 Всего запросов: {user['total_requests']}\n"
        f"🖼️ Всего изображений: {user['total_images']}\n"
        f"👥 Рефералов: {user['ref_count']}\n"
        f"🤖 Основная ИИ: {user['default_ai']}"
    )
    await callback.message.edit_text(text, reply_markup=admin_user_profile_buttons(target_id), parse_mode="Markdown")
    await callback.answer()

# ---------- Начислить баланс ----------
@router.callback_query(lambda c: c.data.startswith("admin_add_balance_"))
async def admin_add_balance_prompt(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    target_id = int(callback.data.split("_")[-1])
    await state.update_data(target_user=target_id)
    await callback.message.answer("💰 Введите количество запросов для начисления (можно отрицательное):")
    await state.set_state(AdminStates.waiting_balance_amount)
    await callback.answer()

@router.message(AdminStates.waiting_balance_amount)
async def admin_add_balance_execute(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("Нет доступа")
        await state.clear()
        return
    try:
        amount = int(message.text.strip())
        data = await state.get_data()
        target_id = data['target_user']
        user = get_user(target_id)
        new_balance = user['balance_requests'] + amount
        if new_balance < 0:
            new_balance = 0
        update_user(target_id, balance_requests=new_balance)
        await message.answer(f"✅ Баланс пользователя {target_id} изменён на {amount}. Теперь: {new_balance} запросов.")
        user = get_user(target_id)
        text = f"👤 **Профиль пользователя** ... (обновлено)"
        await message.answer(text, reply_markup=admin_user_profile_buttons(target_id), parse_mode="Markdown")
    except:
        await message.answer("❌ Ошибка. Введите целое число.")
    finally:
        await state.clear()

# ---------- Выдать подписку ----------
@router.callback_query(lambda c: c.data.startswith("admin_give_sub_"))
async def admin_give_sub(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    target_id = int(callback.data.split("_")[-1])
    from datetime import datetime, timedelta
    until = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    update_user(target_id, subscribed=1, subscription_until=until)
    await callback.answer(f"✅ Подписка на 30 дней выдана пользователю {target_id}")
    user = get_user(target_id)
    text = f"👤 **Профиль пользователя** ... (подписка активна)"
    await callback.message.edit_text(text, reply_markup=admin_user_profile_buttons(target_id), parse_mode="Markdown")

# ---------- Отправить сообщение пользователю ----------
@router.callback_query(lambda c: c.data.startswith("admin_msg_"))
async def admin_msg_prompt(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    target_id = int(callback.data.split("_")[-1])
    await state.update_data(target_user=target_id)
    await callback.message.answer("✏️ Введите текст сообщения, которое будет отправлено пользователю:")
    await state.set_state(AdminStates.waiting_msg_text)
    await callback.answer()

@router.message(AdminStates.waiting_msg_text)
async def admin_send_message(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("Нет доступа")
        await state.clear()
        return
    text = message.text
    data = await state.get_data()
    target_id = data['target_user']
    try:
        await message.bot.send_message(target_id, f"📩 Сообщение от администратора:\n{text}")
        await message.answer(f"✅ Сообщение отправлено пользователю {target_id}")
    except:
        await message.answer(f"❌ Не удалось отправить сообщение пользователю {target_id} (возможно, бот заблокирован).")
    await state.clear()

# ---------- Очистить историю пользователя ----------
@router.callback_query(lambda c: c.data.startswith("admin_clear_history_"))
async def admin_clear_history_user(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    target_id = int(callback.data.split("_")[-1])
    clear_history(target_id)
    await callback.answer(f"🗑 История чата пользователя {target_id} очищена")
    user = get_user(target_id)
    text = f"👤 **Профиль пользователя** ... (история очищена)"
    await callback.message.edit_text(text, reply_markup=admin_user_profile_buttons(target_id), parse_mode="Markdown")

# ---------- История запросов пользователя ----------
@router.callback_query(lambda c: c.data.startswith("admin_user_history_"))
async def admin_user_history(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    target_id = int(callback.data.split("_")[-1])
    history = get_history(target_id, "groq", 20)
    if not history:
        await callback.answer("История пуста", show_alert=True)
        return
    text = f"📜 **Последние диалоги пользователя {target_id} (Groq):**\n\n"
    for role, content in history[-10:]:
        text += f"{role}: {content[:100]}...\n"
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

# ---------- Рассылка ----------
@router.callback_query(lambda c: c.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await callback.message.edit_text("📢 **Рассылка**\nОтправь сообщение (текст) для всех пользователей.", reply_markup=back_button("admin_panel"))
    await state.set_state(AdminStates.waiting_broadcast)
    await callback.answer()

@router.message(AdminStates.waiting_broadcast)
async def admin_broadcast_send(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("Нет доступа")
        await state.clear()
        return
    conn = sqlite3.connect("bot_database.db")
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    success = 0
    for uid in users:
        try:
            await message.send_copy(chat_id=uid)
            success += 1
        except:
            pass
    await message.answer(f"✅ Рассылка завершена. Отправлено {success} из {len(users)} пользователям.", reply_markup=back_button("admin_panel"))
    await state.clear()

# ---------- Управление каналами ----------
@router.callback_query(lambda c: c.data == "admin_channels")
async def admin_channels_menu(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    channels = get_required_channels()
    text = "📢 **Обязательные каналы для подписки:**\n\n"
    if not channels:
        text += "Список пуст.\n"
    else:
        for ch in channels:
            text += f"🆔 {ch['id']} | @{ch['username']} | [ссылка]({ch['link']})\n"
    text += "\nВыбери действие:"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить канал", callback_data="admin_add_channel")],
        [InlineKeyboardButton(text="❌ Удалить канал", callback_data="admin_remove_channel")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel")]
    ])
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown", disable_web_page_preview=True)
    await callback.answer()

@router.callback_query(lambda c: c.data == "admin_add_channel")
async def admin_add_channel_step1(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await callback.message.answer("Введите **числовой ID канала** (например, -1001234567890):\n\nЧтобы получить ID, перешлите любое сообщение из канала в @userinfobot.")
    await state.set_state(AdminStates.waiting_channel_id)
    await callback.answer()

@router.message(AdminStates.waiting_channel_id)
async def admin_add_channel_step2(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("Нет доступа")
        await state.clear()
        return
    try:
        channel_id = int(message.text.strip())
        await state.update_data(channel_id=channel_id)
        await message.answer("Введите **username канала** (без @, например: my_channel):")
        await state.set_state(AdminStates.waiting_channel_username)
    except:
        await message.answer("❌ Неверный ID. Введите число. Отмена операции. Начните заново.")
        await state.clear()

@router.message(AdminStates.waiting_channel_username)
async def admin_add_channel_step3(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("Нет доступа")
        await state.clear()
        return
    username = message.text.strip().lstrip('@')
    await state.update_data(channel_username=username)
    await message.answer("Введите **ссылку-приглашение** канала (например, https://t.me/joinchat/... или https://t.me/username):")
    await state.set_state(AdminStates.waiting_channel_link)

@router.message(AdminStates.waiting_channel_link)
async def admin_add_channel_step4(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("Нет доступа")
        await state.clear()
        return
    link = message.text.strip()
    data = await state.get_data()
    channel_id = data['channel_id']
    username = data['channel_username']
    add_required_channel(channel_id, username, link)
    await message.answer(f"✅ Канал {username} (ID: {channel_id}) добавлен в обязательные для подписки.")
    await state.clear()
    # Показать меню каналов
    channels = get_required_channels()
    text = "📢 **Обязательные каналы для подписки:**\n\n"
    if not channels:
        text += "Список пуст.\n"
    else:
        for ch in channels:
            text += f"🆔 {ch['id']} | @{ch['username']} | [ссылка]({ch['link']})\n"
    text += "\nВыбери действие:"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить канал", callback_data="admin_add_channel")],
        [InlineKeyboardButton(text="❌ Удалить канал", callback_data="admin_remove_channel")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel")]
    ])
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown", disable_web_page_preview=True)

@router.callback_query(lambda c: c.data == "admin_remove_channel")
async def admin_remove_channel_menu(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    channels = get_required_channels()
    if not channels:
        await callback.answer("Нет каналов для удаления", show_alert=True)
        return
    text = "Выберите канал для удаления:\n\n"
    keyboard_buttons = []
    for ch in channels:
        text += f"🆔 {ch['id']} | @{ch['username']}\n"
        keyboard_buttons.append([InlineKeyboardButton(text=f"❌ Удалить {ch['username']}", callback_data=f"admin_del_channel_{ch['id']}")])
    keyboard_buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin_channels")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("admin_del_channel_"))
async def admin_delete_channel(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    channel_id = int(callback.data.split("_")[-1])
    remove_required_channel(channel_id)
    await callback.answer("Канал удалён")
    channels = get_required_channels()
    text = "📢 **Обязательные каналы для подписки:**\n\n"
    if not channels:
        text += "Список пуст.\n"
    else:
        for ch in channels:
            text += f"🆔 {ch['id']} | @{ch['username']} | [ссылка]({ch['link']})\n"
    text += "\nВыбери действие:"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить канал", callback_data="admin_add_channel")],
        [InlineKeyboardButton(text="❌ Удалить канал", callback_data="admin_remove_channel")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel")]
    ])
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown", disable_web_page_preview=True)
