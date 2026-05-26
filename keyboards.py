from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    return InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("🤖 Groq (LLaMA 3)", callback_data="ai_groq"),
        InlineKeyboardButton("🧠 DeepSeek", callback_data="ai_deepseek"),
        InlineKeyboardButton("🎨 Сгенерировать изображение", callback_data="generate_image"),
        InlineKeyboardButton("👤 Профиль", callback_data="profile"),
        InlineKeyboardButton("👥 Рефералы", callback_data="referral"),
        InlineKeyboardButton("⭐ Поддержать", callback_data="donate"),
        InlineKeyboardButton("💎 Подписка", callback_data="subscription")
    )

def back_button(callback_data="main_menu"):
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton("◀️ Назад", callback_data=callback_data)
    )

def admin_panel():
    return InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast"),
        InlineKeyboardButton("👥 Пользователи", callback_data="admin_users"),
        InlineKeyboardButton("◀️ Выход", callback_data="main_menu")
    )