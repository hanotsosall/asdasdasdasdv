from aiogram import Router, types, F
from config import ADMIN_ID
from database import DB_PATH
import sqlite3
from keyboards import admin_panel, back_button

router = Router()

@router.callback_query(F.data == "admin_panel")
async def admin_panel_callback(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return
    await callback.message.edit_text("👑 Админ-панель", reply_markup=admin_panel())
    await callback.answer()

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    users_count = c.fetchone()[0]
    c.execute("SELECT SUM(total_requests) FROM users")
    total_req = c.fetchone()[0] or 0
    conn.close()
    text = f"📊 Статистика\n👥 Пользователей: {users_count}\n📨 Всего запросов: {total_req}"
    await callback.message.edit_text(text, reply_markup=back_button("admin_panel"))
    await callback.answer()