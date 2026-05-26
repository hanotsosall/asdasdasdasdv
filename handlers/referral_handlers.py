from aiogram import Router, types
from aiogram.filters import F
from database import get_user
from keyboards import back_button

router = Router()

@router.callback_query(F.data == "referral")
async def referral_menu(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    bot_username = (await callback.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    user = get_user(user_id)
    text = (
        "👥 **Реферальная система**\n\n"
        f"🔗 Твоя ссылка:\n`{link}`\n\n"
        f"👥 Приглашено друзей: {user['ref_count']}\n"
        "🎁 За каждого друга ты получаешь **+5 запросов**.\n"
        "📤 Отправляй ссылку друзьям!"
    )
    await callback.message.edit_text(text, reply_markup=back_button(), parse_mode="Markdown")
    await callback.answer()
