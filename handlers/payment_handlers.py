from aiogram import Router, types, F
from keyboards import back_button

router = Router()

@router.callback_query(F.data == "donate")
async def donate(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "⭐ **Поддержать проект**\n\n"
        "Скоро здесь появится приём Telegram Stars.\n"
        "Пока можно просто рассказать о боте друзьям 😊",
        reply_markup=back_button()
    )
    await callback.answer()

@router.callback_query(F.data == "subscription")
async def subscription(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "💎 **Подписка**\n\n"
        "Скоро здесь появятся платные тарифы.\n"
        "А пока приглашай друзей и получай бонусные запросы!",
        reply_markup=back_button()
    )
    await callback.answer()