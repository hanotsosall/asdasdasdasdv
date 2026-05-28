import os
import sqlite3
from datetime import datetime, timedelta
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile

from config import ADMIN_ID
from database import (
    get_user, update_user, get_all_users, count_users,
    clear_history, get_history, add_required_channel,
    remove_required_channel, get_required_channels,
    backup_database, get_backup_list, restore_database
)
from keyboards import admin_panel, back_button, admin_user_list_menu, admin_user_profile_buttons

router = Router()

class AdminStates(StatesGroup):
    waiting_broadcast = State()
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

# ---------- Команда /admin ----------
@router.message(Command("admin"))
async def admin_command(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Нет доступа.")
        return
    await message.answer("👑 **Админ-панель**", reply_markup=admin_panel(), parse_mode="HTML")

# ---------- Панель админа ----------
@router.callback_query(lambda c: c.data == "admin_panel")
async def admin_panel_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await callback.message.edit_text("👑 **Админ-панель**\nВыбери действие:", reply_markup=admin_panel(), parse_mode="HTML")
    await callback.answer()

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
    text = (f"📊 <b>Статистика</b>\n👥 Пользователей: {users_count}\n"
            f"📨 Всего запросов: {total_req}\n🖼️ Всего изображений: {total_img}\n"
            f"⭐ Подписка активна у: {subscribed_count}")
    await callback.message.edit_text(text, reply_markup=back_button("admin_panel"), parse_mode="HTML")
    await callback.answer()

# ---------- Список пользователей (пагинация) ----------
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
    text = f"👥 <b>Пользователи</b> (стр. {page+1}/{total_pages}):\n"
    for u in users:
        text += f"🆔 {u['user_id']} | @{u.get('username') or 'no name'} | Баланс: {u['balance_requests']} | Подписка: {'✅' if u['subscribed'] else '❌'}\n"
    await callback.message.edit_text(text, reply_markup=admin_user_list_menu(users, page, total_pages), parse_mode="HTML")
    await callback.answer()

# ---------- Профиль пользователя ----------
@router.callback_query(lambda c: c.data.startswith("admin_user_") and not c.data.startswith("admin_user_history_") and not c.data.startswith("admin_user_clear_"))
async def admin_user_profile(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    target_id = int(callback.data.split("_")[-1])
    user = get_user(target_id)
    text = (
        f"👤 <b>Профиль пользователя</b>\n"
        f"🆔 ID: <code>{user['user_id']}</code>\n"
        f"👤 Username: @{user.get('username') or 'нет'}\n"
        f"💰 Баланс: {user['balance_requests']} запросов\n"
        f"⭐ Подписка: {'✅ Активна' if user['subscribed'] else '❌ Нет'}\n"
        f"📊 Всего запросов: {user['total_requests']}\n"
        f"🖼️ Всего изображений: {user['total_images']}\n"
        f"👥 Рефералов: {user['ref_count']}\n"
        f"🤖 Основная ИИ: {user['default_ai']}"
    )
    await callback.message.edit_text(text, reply_markup=admin_user_profile_buttons(target_id), parse_mode="HTML")
    await callback.answer()

# ---------- Начислить баланс ----------
@router.callback_query(lambda c: c.data.startswith("admin_add_balance_"))
async def admin_add_balance_prompt(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    target_id = int(callback.data.split("_")[-1])
    await state.update_data(target_user=target_id)
    await callback.message.answer("💰 Введите количество запросов для начисления (можно отрицательное):", parse_mode="HTML")
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
        await message.answer(f"✅ Баланс пользователя {target_id} изменён на {amount}. Теперь: {new_balance} запросов.", parse_mode="HTML")
        user = get_user(target_id)
        text = f"👤 <b>Профиль пользователя</b>\n🆔 ID: <code>{user['user_id']}</code>\n💰 Баланс: {user['balance_requests']}"
        await message.answer(text, reply_markup=admin_user_profile_buttons(target_id), parse_mode="HTML")
    except:
        await message.answer("❌ Ошибка. Введите целое число.", parse_mode="HTML")
    finally:
        await state.clear()

# ---------- Выдать подписку ----------
@router.callback_query(lambda c: c.data.startswith("admin_give_sub_"))
async def admin_give_sub(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    target_id = int(callback.data.split("_")[-1])
    until = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    update_user(target_id, subscribed=1, subscription_until=until)
    await callback.answer(f"✅ Подписка на 30 дней выдана пользователю {target_id}", show_alert=True)
    user = get_user(target_id)
    text = f"👤 <b>Профиль пользователя</b>\n🆔 ID: <code>{user['user_id']}</code>\n⭐ Подписка: ✅ Активна до {until}"
    await callback.message.edit_text(text, reply_markup=admin_user_profile_buttons(target_id), parse_mode="HTML")

# ---------- Отправить сообщение ----------
@router.callback_query(lambda c: c.data.startswith("admin_msg_"))
async def admin_msg_prompt(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    target_id = int(callback.data.split("_")[-1])
    await state.update_data(target_user=target_id)
    await callback.message.answer("✏️ Введите текст сообщения для пользователя:", parse_mode="HTML")
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
        await message.bot.send_message(target_id, f"📩 <b>Сообщение от администратора:</b>\n{text}", parse_mode="HTML")
        await message.answer(f"✅ Сообщение отправлено пользователю {target_id}", parse_mode="HTML")
    except:
        await message.answer(f"❌ Не удалось отправить.", parse_mode="HTML")
    await state.clear()

# ---------- Очистить историю пользователя ----------
@router.callback_query(lambda c: c.data.startswith("admin_clear_history_"))
async def admin_clear_history_user(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    target_id = int(callback.data.split("_")[-1])
    clear_history(target_id)
    await callback.answer(f"🗑 История пользователя {target_id} очищена", show_alert=True)
    user = get_user(target_id)
    text = f"👤 <b>Профиль пользователя</b>\n🆔 ID: <code>{user['user_id']}</code>\nИстория чата очищена."
    await callback.message.edit_text(text, reply_markup=admin_user_profile_buttons(target_id), parse_mode="HTML")

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
    text = f"📜 <b>Последние диалоги пользователя {target_id} (Groq):</b>\n\n"
    for role, content in history[-10:]:
        text += f"👤 {role}: {content[:150]}...\n"
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()

# ---------- Рассылка ----------
@router.callback_query(lambda c: c.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await callback.message.edit_text("📢 **Рассылка**\nОтправь сообщение (текст, фото, видео) для всех пользователей.\nНажми «Назад» для отмены.", reply_markup=back_button("admin_panel"), parse_mode="HTML")
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
    await message.answer(f"✅ Рассылка завершена. Отправлено {success} из {len(users)} пользователям.", reply_markup=back_button("admin_panel"), parse_mode="HTML")
    await state.clear()

# ---------- Управление каналами ----------
@router.callback_query(lambda c: c.data == "admin_channels")
async def admin_channels_menu(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    channels = get_required_channels()
    text = "📢 <b>Обязательные каналы для подписки:</b>\n\n"
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
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML", disable_web_page_preview=True)
    await callback.answer()

@router.callback_query(lambda c: c.data == "admin_add_channel")
async def admin_add_channel_step1(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await callback.message.answer("Введите <b>числовой ID канала</b> (например, -1001234567890):\nЧтобы получить ID, перешлите любое сообщение из канала в @userinfobot.", parse_mode="HTML")
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
        await message.answer("Введите <b>username канала</b> (без @, например: my_channel):", parse_mode="HTML")
        await state.set_state(AdminStates.waiting_channel_username)
    except:
        await message.answer("❌ Неверный ID. Введите число. Отмена операции. Начните заново.", parse_mode="HTML")
        await state.clear()

@router.message(AdminStates.waiting_channel_username)
async def admin_add_channel_step3(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("Нет доступа")
        await state.clear()
        return
    username = message.text.strip().lstrip('@')
    await state.update_data(channel_username=username)
    await message.answer("Введите <b>ссылку-приглашение</b> канала (например, https://t.me/joinchat/... или https://t.me/username):", parse_mode="HTML")
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
    await message.answer(f"✅ Канал {username} (ID: {channel_id}) добавлен в обязательные для подписки.", parse_mode="HTML")
    await state.clear()
    channels = get_required_channels()
    text = "📢 <b>Обязательные каналы для подписки:</b>\n\n"
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
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML", disable_web_page_preview=True)

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
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons), parse_mode="HTML")
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
    text = "📢 <b>Обязательные каналы для подписки:</b>\n\n"
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
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML", disable_web_page_preview=True)

# ---------- Бэкап базы данных (кнопка) ----------
@router.callback_query(lambda c: c.data == "admin_backup")
async def admin_backup(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    try:
        backup_path = backup_database()
        document = FSInputFile(backup_path)
        await callback.message.answer_document(
            document=document,
            caption=f"✅ Бэкап создан: {os.path.basename(backup_path)}"
        )
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка создания бэкапа: {e}", parse_mode="HTML")
    await callback.answer()

# ---------- Восстановление данных (меню) ----------
@router.callback_query(lambda c: c.data == "admin_restore_menu")
async def admin_restore_menu(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    backups = get_backup_list()
    if not backups:
        await callback.message.answer("❌ Нет доступных бэкапов.", parse_mode="HTML")
        return
    text = "📂 <b>Выберите бэкап для восстановления:</b>\n\n"
    keyboard = []
    for b in backups:
        text += f"📅 {b['date']} – {b['size']//1024} KB\n"
        keyboard.append([InlineKeyboardButton(text=f"Восстановить {b['date']}", callback_data=f"restore_{b['name']}")])
    keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="HTML")
    await callback.answer()

# ---------- Исполнение восстановления ----------
@router.callback_query(lambda c: c.data.startswith("restore_"))
async def admin_restore_execute(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    backup_name = callback.data.split("_", 1)[1]
    backup_path = os.path.join("backups", backup_name)
    if not os.path.exists(backup_path):
        await callback.message.answer("❌ Файл бэкапа не найден.", parse_mode="HTML")
        return
    safety_backup = backup_database()
    if restore_database(backup_path):
        await callback.message.answer(
            f"✅ База данных восстановлена из бэкапа {backup_name}.\n"
            f"⚠️ Старая БД сохранена как {safety_backup}\n"
            "Рекомендуется перезапустить бота.",
            parse_mode="HTML"
        )
    else:
        await callback.message.answer("❌ Ошибка восстановления.", parse_mode="HTML")
    await callback.answer()
