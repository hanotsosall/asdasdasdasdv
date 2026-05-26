from aiogram import Router, types
from aiogram.filters import Text
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from config import ADMIN_ID
from database import DB_PATH, get_user, update_user
import sqlite3
from keyboards import admin_panel, back_button, admin_user_list_menu

router = Router()

# Состояния для админ-функций
class AdminStates(StatesGroup):
    waiting_broadcast = State()
    waiting_balance_user_id = State()
    waiting_balance_amount = State()
    waiting_sub_user_id = State()
    waiting_sub_days = State()

# Проверка админа
def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

# --- Панель админа ---
@router.callback_query(Text("admin_panel"))
async def admin_panel_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await callback.message.edit_text("👑 **Админ-панель**\nВыбери действие:", reply_markup=admin_panel(), parse_mode="Markdown")
    await callback.answer()

# --- Статистика ---
@router.callback_query(Text("admin_stats"))
async def admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    conn = sqlite3.connect(DB_PATH)
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

# --- Список пользователей (пагинация) ---
@router.callback_query(Text(startswith="admin_users"))
async def admin_users(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    # Определяем страницу
    data = callback.data
    if "page_" in data:
        page = int(data.split("_")[-1])
    else:
        page = 0
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    total = c.fetchone()[0]
    limit = 5
    offset = page * limit
    c.execute("SELECT user_id, username, balance_requests, subscribed FROM users LIMIT ? OFFSET ?", (limit, offset))
    users = [dict(row) for row in c.fetchall()]
    total_pages = (total + limit - 1) // limit
    conn.close()
    text = f"👥 **Пользователи** (стр. {page+1}/{total_pages}):\n"
    for u in users:
        text += f"🆔 {u['user_id']} | {u.get('username') or 'no name'} | Баланс: {u['balance_requests']} | Подписка: {'✅' if u['subscribed'] else '❌'}\n"
    await callback.message.edit_text(text, reply_markup=admin_user_list_menu(users, page, total_pages), parse_mode="Markdown")
    await callback.answer()

# --- Накрутка баланса (FSM) ---
@router.callback_query(Text("admin_balance"))
async def admin_balance_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await callback.message.edit_text("💰 **Накрутка баланса**\nВведите **user_id** пользователя:", reply_markup=back_button("admin_panel"), parse_mode="Markdown")
    await state.set_state(AdminStates.waiting_balance_user_id)
    await callback.answer()

@router.message(AdminStates.waiting_balance_user_id)
async def admin_balance_get_user(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("Нет доступа")
        await state.clear()
        return
    try:
        user_id = int(message.text.strip())
        await state.update_data(target_user=user_id)
        await message.answer("Введите **количество запросов** (можно отрицательное для списания):", reply_markup=back_button("admin_panel"))
        await state.set_state(AdminStates.waiting_balance_amount)
    except:
        await message.answer("❌ Неверный user_id. Попробуй ещё раз или нажми «Назад».", reply_markup=back_button("admin_panel"))

@router.message(AdminStates.waiting_balance_amount)
async def admin_balance_set(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("Нет доступа")
        await state.clear()
        return
    try:
        amount = int(message.text.strip())
        data = await state.get_data()
        target_user = data['target_user']
        user = get_user(target_user)
        new_balance = user['balance_requests'] + amount
        if new_balance < 0:
            new_balance = 0
        update_user(target_user, balance_requests=new_balance)
        await message.answer(f"✅ Баланс пользователя {target_user} изменён на {amount}. Теперь: {new_balance} запросов.", reply_markup=back_button("admin_panel"))
    except:
        await message.answer("❌ Ошибка. Введите целое число.", reply_markup=back_button("admin_panel"))
    finally:
        await state.clear()

# --- Управление подпиской (FSM) ---
@router.callback_query(Text("admin_subscription"))
async def admin_sub_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await callback.message.edit_text("⭐ **Управление подпиской**\nВведите **user_id** пользователя:", reply_markup=back_button("admin_panel"), parse_mode="Markdown")
    await state.set_state(AdminStates.waiting_sub_user_id)
    await callback.answer()

@router.message(AdminStates.waiting_sub_user_id)
async def admin_sub_get_user(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("Нет доступа")
        await state.clear()
        return
    try:
        user_id = int(message.text.strip())
        await state.update_data(target_user=user_id)
        await message.answer("Введите **количество дней подписки** (0 – отключить, 30 – месяц и т.д.):", reply_markup=back_button("admin_panel"))
        await state.set_state(AdminStates.waiting_sub_days)
    except:
        await message.answer("❌ Неверный user_id.", reply_markup=back_button("admin_panel"))

@router.message(AdminStates.waiting_sub_days)
async def admin_sub_set(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("Нет доступа")
        await state.clear()
        return
    try:
        days = int(message.text.strip())
        data = await state.get_data()
        target_user = data['target_user']
        from datetime import datetime, timedelta
        if days <= 0:
            update_user(target_user, subscribed=0, subscription_until=None)
            await message.answer(f"✅ Подписка пользователя {target_user} отключена.", reply_markup=back_button("admin_panel"))
        else:
            until = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
            update_user(target_user, subscribed=1, subscription_until=until)
            await message.answer(f"✅ Пользователю {target_user} выдана подписка на {days} дней.\nДействует до {until}.", reply_markup=back_button("admin_panel"))
    except:
        await message.answer("❌ Ошибка. Введите целое число дней.", reply_markup=back_button("admin_panel"))
    finally:
        await state.clear()

# --- Рассылка (FSM) ---
@router.callback_query(Text("admin_broadcast"))
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await callback.message.edit_text("📢 **Рассылка**\nОтправь сообщение (текст) для всех пользователей.\nМожно с фото/видео – бот перешлёт.", reply_markup=back_button("admin_panel"))
    await state.set_state(AdminStates.waiting_broadcast)
    await callback.answer()

@router.message(AdminStates.waiting_broadcast)
async def admin_broadcast_send(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("Нет доступа")
        await state.clear()
        return
    conn = sqlite3.connect(DB_PATH)
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
