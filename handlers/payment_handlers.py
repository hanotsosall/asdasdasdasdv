from aiogram import Router
from aiogram.types import CallbackQuery
from keyboards import back_button

router = Router()

@router.callback_query(lambda c: c.data == "donate")
async def donate(callback: CallbackQuery):
    await callback.message.edit_text(
        "⭐ **Поддержать проект**\n\nСкоро здесь появится приём Telegram Stars.",
        reply_markup=back_button()
    )
    await callback.answer()

@router.callback_query(lambda c: c.data == "subscription")
async def subscription(callback: CallbackQuery):
    await callback.message.edit_text(
        "💎 **Подписка**\n\nСкоро здесь появятся платные тарифы.",
        reply_markup=back_button()
    )
    await callback.answer()
