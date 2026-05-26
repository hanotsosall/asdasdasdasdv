from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🤖 Groq (LLaMA 3)", callback_data="ai_groq"),
            InlineKeyboardButton(text="🧠 DeepSeek", callback_data="ai_deepseek")
        ],
        [
            InlineKeyboardButton(text="🎨 Сгенерировать изображение", callback_data="generate_image")
        ],
        [
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
            InlineKeyboardButton(text="👥 Рефералы", callback_data="referral")
        ],
        [
            InlineKeyboardButton(text="⭐ Поддержать", callback_data="donate"),
            InlineKeyboardButton(text="💎 Подписка", callback_data="subscription")
        ]
    ])

def back_button(callback_data="main_menu"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data=callback_data)]
    ])

def admin_panel():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton(text="◀️ Выход", callback_data="main_menu")]
    ])
