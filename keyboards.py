from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from config import ADMIN_ID

def main_menu(user_id: int):
    buttons = [
        [
            InlineKeyboardButton(text="🤖 Groq (LLaMA 3)", callback_data="ai_groq"),
            InlineKeyboardButton(text="🧠 DeepSeek", callback_data="ai_deepseek")
        ],
        [
            InlineKeyboardButton(text="🎨 Генерация изображения", callback_data="generate_image_menu")
        ],
        [
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
            InlineKeyboardButton(text="👥 Рефералы", callback_data="referral"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")
        ],
        [
            InlineKeyboardButton(text="⭐ Поддержать (Telegram Stars)", callback_data="donate"),
            InlineKeyboardButton(text="💎 Подписка / Запросы", callback_data="donate")
        ],
        [
            InlineKeyboardButton(text="🎮 Открыть Mini App", web_app=WebAppInfo(url="https://asdasdasdasdv-production.up.railway.app"))
        ]
    ]
    # Скрытая кнопка для админа
    if user_id == ADMIN_ID:
        buttons.append([InlineKeyboardButton(text="👑 Админ-панель", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def back_button(callback_data="main_menu"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data=callback_data)]
    ])

def admin_panel():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton(text="💰 Накрутка баланса", callback_data="admin_balance")],
        [InlineKeyboardButton(text="⭐ Управление подпиской", callback_data="admin_subscription")],
        [InlineKeyboardButton(text="◀️ Выход", callback_data="main_menu")]
    ])

def admin_user_list_menu(users: list, page: int, total_pages: int):
    """Генерирует клавиатуру для списка пользователей с пагинацией"""
    buttons = []
    for u in users[:5]:  # показываем 5 на странице
        text = f"{u['user_id']} | {u.get('username', 'no name')} | {u['balance_requests']} запр."
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"admin_user_{u['user_id']}")])
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("◀️ Назад", callback_data=f"admin_users_page_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Вперед ▶️", callback_data=f"admin_users_page_{page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)
    buttons.append([InlineKeyboardButton("◀️ В админ-панель", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
