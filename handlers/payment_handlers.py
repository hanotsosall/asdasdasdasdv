from aiogram import Router, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import get_user, update_user
from config import ADMIN_ID

router = Router()

class PaymentStates(StatesGroup):
    waiting_receipt = State()

@router.callback_query(lambda c: c.data == "donate")
async def donate_menu(callback: types.CallbackQuery):
    text = (
        "⭐ **Поддержать проект**\n\n"
        "Вы можете приобрести:\n"
        "🎁 **10 запросов** – 50₽\n"
        "🎁 **50 запросов** – 200₽\n"
        "🎁 **100 запросов** – 350₽\n"
        "👑 **Подписка на 30 дней (безлимит)** – 500₽\n\n"
        "**Как оплатить:**\n"
        "1. Переведите нужную сумму на карту: `XXXX XXXX XXXX XXXX`\n"
        "2. Отправьте **чек оплаты** (скриншот) в этот чат.\n"
        "3. Администратор проверит и начислит запросы.\n\n"
        "После оплаты нажмите кнопку **«Я оплатил(а)»**."
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
async def buy_product(callback: types.CallbackQuery, state: FSMContext):
    product_key = callback.data.replace("buy_", "")
    await state.update_data(product=product_key)
    await callback.message.answer(
        f"✅ Вы выбрали товар.\n\n"
        f"**Реквизиты для оплаты:**\n"
        f"Тинькофф: `+7 XXX XXX-XX-XX`\n"
        f"Сбербанк: `XXXX XXXX XXXX XXXX`\n"
        f"USDT (TRC20): `TXxx...`\n\n"
        f"После перевода нажмите **«Я оплатил(а)»** и пришлите чек.\n"
        f"Укажите в комментарии ID: `{callback.from_user.id}`"
    )
    await callback.answer()

@router.callback_query(lambda c: c.data == "payment_done")
async def payment_done(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("📸 Отправьте чек (фото или скриншот). Администратор проверит.")
    await state.set_state(PaymentStates.waiting_receipt)
    await callback.answer()

@router.message(PaymentStates.waiting_receipt)
async def handle_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    product = data.get("product", "неизвестно")
    admin_text = (
        f"📢 **Новый платёж**\n"
        f"👤 User ID: {message.from_user.id}\n"
        f"📦 Товар: {product}\n"
        f"💬 Сообщение: {message.text if message.text else 'Фото'}"
    )
    await message.bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
    if message.photo:
        await message.bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption="Чек")
    elif message.document:
        await message.bot.send_document(ADMIN_ID, message.document.file_id, caption="Чек")
    else:
        await message.bot.send_message(ADMIN_ID, message.text)
    await message.answer("✅ Чек отправлен. Ожидайте начисления.")
    await state.clear()

@router.message(Command("add_balance"))
async def admin_add_balance(message: types.Message):
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
        await message.answer(f"✅ Добавлено {amount} запросов пользователю {user_id}. Баланс: {new_balance}")
        await message.bot.send_message(user_id, f"💰 Вам начислено {amount} запросов! Новый баланс: {new_balance}")
    except:
        await message.answer("Ошибка. Проверьте ID и сумму.")
