from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import get_user, update_user
from config import ADMIN_ID

router = Router()

# Состояния для ожидания чека
class PaymentStates(StatesGroup):
    waiting_receipt = State()

@router.callback_query(lambda c: c.data == "donate")
async def donate_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    text = (
        "⭐ **Поддержать проект**\n\n"
        "Вы можете приобрести:\n"
        "🎁 **10 запросов** – 50₽\n"
        "🎁 **50 запросов** – 200₽\n"
        "🎁 **100 запросов** – 350₽\n"
        "👑 **Подписка на 30 дней (безлимит)** – 500₽\n\n"
        "**Как оплатить:**\n"
        "1. Переведите нужную сумму на карту: `2200 7021 2282 7293` Т-Банк\n"
        "2. Отправьте **чек оплаты** (скриншот или фото) в этот чат.\n"
        "3. Администратор проверит оплату и начислит запросы.\n\n"
        "💡 Ожидание обычно до 5 минут.\n"
        "После оплаты нажмите кнопку **«Я оплатил(а)»** и пришлите чек."
    )
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="💎 10 запросов (50₽)", callback_data="buy_balance_10")],
        [types.InlineKeyboardButton(text="💎 50 запросов (200₽)", callback_data="buy_balance_50")],
        [types.InlineKeyboardButton(text="💎 100 запросов (350₽)", callback_data="buy_balance_100")],
        [types.InlineKeyboardButton(text="👑 Подписка (500₽)", callback_data="buy_subscription")],
        [types.InlineKeyboardButton(text="✅ Я оплатил(а)", callback_data="payment_done")],
        [types.InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("buy_"))
async def buy_product(callback: CallbackQuery, state: FSMContext):
    product_key = callback.data.replace("buy_", "")
    prices = {
        "balance_10": "50₽ (10 запросов)",
        "balance_50": "200₽ (50 запросов)",
        "balance_100": "350₽ (100 запросов)",
        "subscription": "500₽ (подписка 30 дней)"
    }
    amount_info = prices.get(product_key, "неизвестно")
    await state.update_data(product=product_key)
    await callback.message.answer(
        f"Вы выбрали **{amount_info}**.\n\n"
        f"**Реквизиты для оплаты:**\n"
        f"Т-Банк: `2200 7021 2282 7293`\n"
        f"Сбербанк: `2202  2080 8392 4705`\n\n"
        f"После перевода нажмите кнопку **«Я оплатил(а)»** и пришлите чек боту.\n\n"
        f"Не забудьте указать в комментарии **Ваш Telegram ID**: `{callback.from_user.id}`"
    )
    await callback.answer()

@router.callback_query(lambda c: c.data == "payment_done")
async def payment_done(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("📸 Отправьте **чек оплаты** (скриншот или фото) в этот чат. Администратор проверит и начислит запросы.")
    await state.set_state(PaymentStates.waiting_receipt)
    await callback.answer()

@router.message(PaymentStates.waiting_receipt)
async def handle_receipt(message: Message, state: FSMContext):
    user_id = message.from_user.id
    # Отправляем админу сообщение с чеком и данными пользователя
    data = await state.get_data()
    product = data.get("product", "неизвестно")
    admin_text = (
        f"📢 **Новый платёж от пользователя**\n"
        f"🆔 ID: {user_id}\n"
        f"👤 Username: @{message.from_user.username or 'нет'}\n"
        f"📦 Товар: {product}\n"
        f"💬 Сообщение пользователя:\n{message.text if message.text else 'Фото чека приложено'}"
    )
    # Пересылаем сообщение админу (текст + медиа)
    await message.bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
    if message.photo:
        await message.bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption="Чек оплаты")
    elif message.document:
        await message.bot.send_document(ADMIN_ID, message.document.file_id, caption="Чек оплаты")
    else:
        await message.bot.send_message(ADMIN_ID, "Текст чека (без картинки):\n" + message.text)
    
    await message.answer("✅ Чек отправлен администратору. Ожидайте начисления (обычно до 5 минут). Спасибо за поддержку!")
    await state.clear()

# Команда для админа: начислить запросы (вручную, после проверки)
@router.message(Command("add_balance"))
async def admin_add_balance(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) != 3:
        await message.answer("Использование: /add_balance <user_id> <количество>")
        return
    try:
        user_id = int(args[1])
        amount = int(args[2])
        user = get_user(user_id)
        new_balance = user['balance_requests'] + amount
        update_user(user_id, balance_requests=new_balance)
        await message.answer(f"✅ Пользователю {user_id} добавлено {amount} запросов. Баланс: {new_balance}")
        await message.bot.send_message(user_id, f"💰 Вам начислено **{amount}** запросов! Новый баланс: {new_balance}", parse_mode="Markdown")
    except:
        await message.answer("Ошибка. Проверьте ID и количество.")
