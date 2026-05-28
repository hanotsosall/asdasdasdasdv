from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import sqlite3
from database import backup_database, get_backup_list, restore_database
import os

from config import ADMIN_ID
from database import (
    get_user, update_user, get_all_users, count_users,
    clear_history, get_history, add_history
)
from keyboards import admin_panel, back_button, admin_user_list_menu, admin_user_profile_buttons

router = Router()

# Состояния для FSM
class AdminStates(StatesGroup):
    waiting_broadcast = State()
    waiting_balance_amount = State()
    waiting_sub_user_id = State()
    waiting_sub_days = State()
    waiting_msg_user_id = State()
    waiting_msg_text = State()

# Проверка админа
def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

# ---------- Команда /admin (для надёжного доступа) ----------
@router.message(Command("admin"))
async def admin_command(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Нет доступа.")
        return
    await message.answer("👑 **Админ-панель**", reply_markup=admin_panel(), parse_mode="Markdown")

# ---------- Обработчик кнопки "Админ-панель" ----------
@router.callback_query(lambda c: c.data == "admin_panel")
async def admin_panel_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await callback.message.edit_text("👑 **Админ-панель**\nВыбери действие:", reply_markup=admin_panel(), parse_mode="Markdown")
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
    text = (f"📊 **Статистика**\n👥 Пользователей: {users_count}\n"
            f"📨 Всего запросов: {total_req}\n🖼️ Всего изображений: {total_img}\n"
            f"⭐ Подписка активна у: {subscribed_count}")
    await callback.message.edit_text(text, reply_markup=back_button("admin_panel"), parse_mode="Markdown")
    await callback.answer()

# ---------- Список пользователей (пагинация) ----------
@router.callback_query(lambda c: c.data.startswith("admin_users"))
async def admin_users(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    # Определяем номер страницы
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
        text += f"🆔 {u['user_id']} | @{u.get('username') or 'no name'} | Баланс: {u['balance_requests']} | Подписка: {'✅' if u['subscribed'] else '❌'}\n"
    await callback.message.edit_text(text, reply_markup=admin_user_list_menu(users, page, total_pages), parse_mode="Markdown")
    await callback.answer()

# ---------- Просмотр профиля пользователя (по клику на пользователя) ----------
@router.callback_query(lambda c: c.data.startswith("admin_user_") and not c.data.startswith("admin_user_history_") and not c.data.startswith("admin_user_clear_"))
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

# ---------- Накрутка баланса (кнопка в профиле) ----------
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
        # Показываем профиль снова
        user = get_user(target_id)
        text = (
            f"👤 **Профиль пользователя**\n"
            f"🆔 ID: `{user['user_id']}`\n"
            f"💰 Баланс: {user['balance_requests']} запросов\n"
            f"⭐ Подписка: {'✅ Активна' if user['subscribed'] else '❌ Нет'}"
        )
        await message.answer(text, reply_markup=admin_user_profile_buttons(target_id), parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}. Введите целое число.")
    finally:
        await state.clear()

# ---------- Выдача подписки (кнопка в профиле) ----------
@router.callback_query(lambda c: c.data.startswith("admin_give_sub_"))
async def admin_give_sub(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    target_id = int(callback.data.split("_")[-1])
    until = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    update_user(target_id, subscribed=1, subscription_until=until)
    await callback.answer(f"✅ Подписка на 30 дней выдана пользователю {target_id}", show_alert=True)
    # Обновляем профиль
    user = get_user(target_id)
    text = (
        f"👤 **Профиль пользователя**\n"
        f"🆔 ID: `{user['user_id']}`\n"
        f"💰 Баланс: {user['balance_requests']}\n"
        f"⭐ Подписка: ✅ Активна до {until}"
    )
    await callback.message.edit_text(text, reply_markup=admin_user_profile_buttons(target_id), parse_mode="Markdown")

# ---------- Отправить сообщение пользователю ----------
@router.callback_query(lambda c: c.data.startswith("admin_msg_"))
async def admin_msg_prompt(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    target_id = int(callback.data.split("_")[-1])
    await state.update_data(target_user=target_id)
    await callback.message.answer("✏️ Введите текст сообщения для пользователя:")
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
    except Exception as e:
        await message.answer(f"❌ Не удалось отправить: {e}")
    await state.clear()

# ---------- Очистить историю чата пользователя ----------
@router.callback_query(lambda c: c.data.startswith("admin_clear_history_"))
async def admin_clear_history_user(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    target_id = int(callback.data.split("_")[-1])
    clear_history(target_id)
    await callback.answer(f"🗑 История пользователя {target_id} очищена", show_alert=True)
    # Обновляем профиль
    user = get_user(target_id)
    text = f"👤 **Профиль пользователя**\n🆔 ID: `{user['user_id']}`\nИстория чата очищена."
    await callback.message.edit_text(text, reply_markup=admin_user_profile_buttons(target_id), parse_mode="Markdown")

# ---------- История запросов пользователя ----------
@router.callback_query(lambda c: c.data.startswith("admin_user_history_"))
async def admin_user_history(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    target_id = int(callback.data.split("_")[-1])
    history = get_history(target_id, "groq", 20)  # последние 20 сообщений (можно взять любую модель)
    if not history:
        await callback.answer("История пуста", show_alert=True)
        return
    text = f"📜 **Последние диалоги пользователя {target_id} (Groq):**\n\n"
    for role, content in history[-10:]:
        text += f"👤 {role}: {content[:150]}...\n"
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

# ---------- Рассылка ----------
@router.callback_query(lambda c: c.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await callback.message.edit_text("📢 **Рассылка**\nОтправь сообщение (текст, фото, видео) для всех пользователей.\nНажми «Назад» для отмены.", reply_markup=back_button("admin_panel"))
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
  
