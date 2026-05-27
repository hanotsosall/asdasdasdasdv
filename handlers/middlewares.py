from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from typing import Callable, Dict, Any, Awaitable
from database import get_required_channels
from config import ADMIN_ID

class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, Message):
            user_id = event.from_user.id
        else:
            user_id = event.from_user.id

        # Администратора не проверяем
        if user_id == ADMIN_ID:
            return await handler(event, data)

        # Команду /start и кнопку "Проверить подписку" пропускаем
        if isinstance(event, Message) and event.text and event.text.startswith("/start"):
            return await handler(event, data)
        if isinstance(event, CallbackQuery) and event.data == "check_subscription":
            return await handler(event, data)

        channels = get_required_channels()
        if not channels:
            return await handler(event, data)

        bot = data.get("bot")
        if not bot:
            return await handler(event, data)

        not_subscribed = []
        for ch in channels:
            try:
                member = await bot.get_chat_member(chat_id=ch["id"], user_id=user_id)
                if member.status in ("left", "kicked"):
                    not_subscribed.append(ch)
            except:
                not_subscribed.append(ch)

        if not_subscribed:
            text = "🔒 **Для использования бота необходимо подписаться на следующие каналы:**\n\n"
            keyboard_buttons = []
            for ch in not_subscribed:
                if ch["link"]:
                    text += f"• [{ch['username'] or ch['id']}]({ch['link']})\n"
                    keyboard_buttons.append([InlineKeyboardButton(text=f"📢 Подписаться", url=ch["link"])])
                else:
                    text += f"• {ch['username'] or ch['id']}\n"
            keyboard_buttons.append([InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_subscription")])
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

            if isinstance(event, Message):
                await event.answer(text, reply_markup=keyboard, parse_mode="Markdown", disable_web_page_preview=True)
            else:
                await event.message.answer(text, reply_markup=keyboard, parse_mode="Markdown", disable_web_page_preview=True)
                await event.answer()
            return

        return await handler(event, data)
