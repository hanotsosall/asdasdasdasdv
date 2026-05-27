from aiogram import Router, types
from aiogram.filters.command import Command
from database import get_user, add_referral
from keyboards import main_menu

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref_"):
        ref_id = int(args[1].split("_")[1])
        if ref_id != user_id:
            add_referral(ref_id, user_id)
    user = get_user(user_id)
    text = (
        "🚀 <b>Ultimate AI Bot</b>\n\n"
        "Я объединяю <b>Groq (LLaMA 3)</b> и <b>Google Gemini (Временно не работает)</b> – две мощные нейросети.\n"
        "🎨 Генерирую изображения по тексту.\n\n"
        f"💎 У тебя осталось <b>{user['balance_requests']}</b> бесплатных запросов.\n"
        "➕ Приглашай друзей (+5 запросов за каждого).\n"
        "👇 Выбери действие:"
    )
    await message.answer(text, reply_markup=main_menu(user_id), parse_mode="HTML")

@router.callback_query(lambda c: c.data == "main_menu")
async def back_to_main_menu(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user = get_user(user_id)
    text = (
        "🚀 <b>Ultimate AI Bot</b>\n\n"
        "Я объединяю <b>Groq</b> и <b>Gemini</b>.\n"
        "🎨 Генерирую изображения.\n\n"
        f"💎 У тебя осталось <b>{user['balance_requests']}</b> запросов.\n"
        "👇 Выбери действие:"
    )
    await callback.message.edit_text(text, reply_markup=main_menu(user_id), parse_mode="HTML")
    await callback.answer()

@router.callback_query(lambda c: c.data == "check_subscription")
async def check_subscription_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    bot = callback.bot
    channels = get_required_channels()
    not_subscribed = []
    for ch in channels:
        try:
            member = await bot.get_chat_member(chat_id=ch["id"], user_id=user_id)
            if member.status in ("left", "kicked"):
                not_subscribed.append(ch)
        except:
            not_subscribed.append(ch)
    if not_subscribed:
        text = "❌ Вы не подписались на следующие каналы:\n\n"
        keyboard_buttons = []
        for ch in not_subscribed:
            if ch["link"]:
                text += f"• [{ch['username'] or ch['id']}]({ch['link']})\n"
                keyboard_buttons.append([types.InlineKeyboardButton(text="📢 Подписаться", url=ch["link"])])
            else:
                text += f"• {ch['username'] or ch['id']}\n"
        keyboard_buttons.append([types.InlineKeyboardButton(text="✅ Проверить снова", callback_data="check_subscription")])
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown", disable_web_page_preview=True)
        await callback.answer()
    else:
        user = get_user(user_id)
        text = (
            "🚀 <b>Ultimate AI Bot</b>\n\n"
            "✅ Вы подписались на все обязательные каналы!\n\n"
            f"💎 У тебя осталось <b>{user['balance_requests']}</b> бесплатных запросов.\n"
            "👇 Выбери действие:"
        )
        from keyboards import main_menu
        await callback.message.edit_text(text, reply_markup=main_menu(user_id), parse_mode="HTML")
        await callback.answer("Подписка подтверждена!")
