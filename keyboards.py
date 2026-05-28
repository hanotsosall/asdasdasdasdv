from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from config import ADMIN_ID

def main_menu(user_id: int):
    buttons = [
        [
            InlineKeyboardButton(text="🤖 Groq (LLaMA 3)", callback_data="ai_groq"),
            InlineKeyboardButton(text="✨ Gemini (1.5 Flash)", callback_data="ai_gemini")
            InlineKeyboardButton(text="🤬 NeuroHam", callback_data="ai_neurohama")
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
            InlineKeyboardButton(text="⭐ Поддержать / Купить", callback_data="donate")
        ],
        [
            InlineKeyboardButton(text="🎮 Открыть Mini App", web_app=WebAppInfo(url="https://asdasdasdasdv-production.up.railway.app"))
        ]
    ]
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
        [InlineKeyboardButton(text="👥 Список пользователей", callback_data="admin_users")],
        [InlineKeyboardButton(text="💰 Накрутка баланса", callback_data="admin_balance")],
        [InlineKeyboardButton(text="⭐ Управление подпиской", callback_data="admin_subscription")],
        [InlineKeyboardButton(text="💾 Бэкап БД", callback_data="admin_backup")],
        [InlineKeyboardButton(text="🔄 Восстановить данные", callback_data="admin_restore_menu")],
        [InlineKeyboardButton(text="◀️ Выход", callback_data="main_menu")]
    ])

def admin_user_list_menu(users: list, page: int, total_pages: int):
    buttons = []
    for u in users:
        text = f"{u['user_id']} | {u.get('username') or 'no name'} | {u['balance_requests']} запр."
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"admin_user_{u['user_id']}")])
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("◀️ Назад", callback_data=f"admin_users_page_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Вперед ▶️", callback_data=f"admin_users_page_{page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)
    buttons.append([InlineKeyboardButton(text="◀️ В админ-панель", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_user_profile_buttons(user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Начислить баланс", callback_data=f"admin_add_balance_{user_id}")],
        [InlineKeyboardButton(text="⭐ Выдать подписку (30 дней)", callback_data=f"admin_give_sub_{user_id}")],
        [InlineKeyboardButton(text="✏️ Отправить сообщение", callback_data=f"admin_msg_{user_id}")],
        [InlineKeyboardButton(text="🗑 Очистить историю чата", callback_data=f"admin_clear_history_{user_id}")],
        [InlineKeyboardButton(text="📜 История запросов", callback_data=f"admin_user_history_{user_id}")],
        [InlineKeyboardButton(text="◀️ Назад к списку", callback_data="admin_users")],
        [InlineKeyboardButton(text="◀️ В админ-панель", callback_data="admin_panel")]
    ])

def settings_menu(current_ai: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🤖 Основная ИИ: {current_ai.upper()}", callback_data="change_default_ai")],
        [InlineKeyboardButton(text="🗑 Очистить историю диалога", callback_data="clear_history")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
    ])

def ai_choice_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Groq", callback_data="set_ai_groq"),
         InlineKeyboardButton(text="Gemini", callback_data="set_ai_gemini")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="settings")]
    ])

def image_generation_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎨 Сгенерировать изображение", callback_data="generate_image")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
    ])
