from aiogram import Router
from aiogram.types import CallbackQuery
from database import get_user
from keyboards import back_button

router = Router()

@router.callback_query(lambda c: c.data == "profile")
async def profile(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    text = (
        "👤 <b>Профиль</b>\n\n"
        f"🆔 ID: <code>{user['user_id']}</code>\n"
        f"💰 Баланс запросов: <b>{user['balance_requests']}</b>\n"
        f"👥 Приглашено друзей: {user['ref_count']}\n"
        f"📊 Всего запросов: {user['total_requests']}\n"
        f"🖼️ Всего изображений: {user['total_images']}\n"
        f"⭐ Подписка: {'✅ Активна' if user['subscribed'] else '❌ Неактивна'}"
    )
    await callback.message.edit_text(text, reply_markup=back_button(), parse_mode="HTML")
    await callback.answer()
