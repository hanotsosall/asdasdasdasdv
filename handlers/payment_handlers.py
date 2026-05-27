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
        "⭐ <b>Поддержать проект</b>\n\n"
        "Вы можете приобрести:\n"
        "🎁 <b>10 запросов</b> – 50₽\n"
        "🎁 <b>50 запросов</b> – 200₽\n"
        "🎁 <b>100 запросов</b> – 350₽\n"
        "👑 <b>Подписка на 30 дней (безлимит)</b> – 500₽\n\n"
        "Как оплатить:\n"
        "1. Переведите нужную сумму на карту: <code>XXXX XXXX XXXX XXXX</code>\n"
        "2. Отправьте чек (скриншот) в этот чат.\n"
        "3. Администратор проверит и начислит запросы.\n\n"
        "После оплаты нажмите <b>«Я оплатил(а)»</b>."
    )
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="💎 10 запросов (50₽)", callback_data="buy_balance_10")],
        [types.InlineKeyboardButton(text="💎 50 запросов (200₽)", callback_data="buy_balance_50")],
        [types.InlineKeyboardButton(text="💎 100 запросов (350₽)", callback_data="buy_balance_100")],
        [types.InlineKeyboardButton(text="👑 Подписка (500₽)", callback_data="buy_subscription")],
        [types.InlineKeyboardButton(text="✅ Я оплатил(а)", callback_data="payment_done")],
        [types.InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("buy_"))
async def buy_product(callback: types.CallbackQuery, state: FSMContext):
    product_key = callback.data.replace("buy_", "")
    await state.update_data(product=product_key)
    await callback.message.answer(
        f"✅ Вы выбрали товар.\n\n"
        f"<b>Реквизиты для оплаты:</b>\n"
        f"Тинькофф: <code>+7 XXX XXX-XX-XX</code>\n"
        f"Сбербанк: <code>XXXX XXXX XXXX XXXX</code>\n\n"
        f"После перевода нажмите <b>«Я оплатил(а)»</b> и пришлите чек.\n"
        f"Укажите в комментарии ID: <code>{callback.from_user.id}</code>",
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(lambda c: c.data == "payment_done")
async def payment_done(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("📸 Отправьте чек (фото или скриншот). Администратор проверит.", parse_mode="HTML")
    await state.set_state(PaymentStates.waiting_receipt)
    await callback.answer()

@router.message(PaymentStates.waiting_receipt)
async def handle_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    product = data.get("product", "неизвестно")
    admin_text = (
        f"📢 <b>Новый платёж</b>\n"
        f"👤 User ID: <code>{message.from_user.id}</code>\n"
        f"📦 Товар: {product}"
    )
    await message.bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML")
    if message.photo:
        await message.bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption="Чек")
    elif message.document:
        await message.bot.send_document(ADMIN_ID, message.document.file_id, caption="Чек")
    else:
        await message.bot.send_message(ADMIN_ID, message.text)
    await message.answer("✅ Чек отправлен. Ожидайте начисления.", parse_mode="HTML")
    await state.clear()

@router.message(Command("add_balance"))
async def admin_add_balance(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) != 3:
        await message.answer("Использование: /add_balance <user_id> <количество>", parse_mode="HTML")
        return
    try:
        user_id = int(args[1])
        amount = int(args[2])
        user = get_user(user_id)
        new_balance = user['balance_requests'] + amount
        update_user(user_id, balance_requests=new_balance)
        await message.answer(f"✅ Добавлено {amount} запросов пользователю {user_id}. Баланс: {new_balance}", parse_mode="HTML")
        await message.bot.send_message(user_id, f"💰 Вам начислено {amount} запросов! Новый баланс: {new_balance}", parse_mode="HTML")
    except:
        await message.answer("Ошибка. Проверьте ID и сумму.", parse_mode="HTML")
