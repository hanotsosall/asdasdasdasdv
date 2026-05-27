from aiogram import Router
from aiogram.types import CallbackQuery
from database import get_user
from keyboards import back_button

router = Router()

@router.callback_query(lambda c: c.data == "referral")
async def referral_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    bot_username = (await callback.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    user = get_user(user_id)
    text = (
        "👥 <b>Реферальная система</b>\n\n"
        f"🔗 Твоя ссылка:\n<code>{link}</code>\n\n"
        f"👥 Приглашено друзей: <b>{user['ref_count']}</b>\n"
        "🎁 За каждого друга ты получаешь <b>+5 запросов</b>.\n"
        "📤 Отправляй ссылку друзьям!"
    )
    await callback.message.edit_text(text, reply_markup=back_button(), parse_mode="HTML")
    await callback.answer()
