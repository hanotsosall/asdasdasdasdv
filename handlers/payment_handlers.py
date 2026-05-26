from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery, SuccessfulPayment, CallbackQuery
from datetime import datetime, timedelta
from database import get_user, update_user
import sqlite3
from config import DB_PATH

router = Router()

# Товары для продажи
PRODUCTS = {
    "balance_10": {
        "title": "10 дополнительных запросов",
        "description": "Пополнение баланса AI запросов",
        "price": 5,  # в Telegram Stars
        "type": "balance",
        "amount": 10
    },
    "balance_50": {
        "title": "50 дополнительных запросов",
        "description": "Пополнение баланса AI запросов",
        "price": 20,
        "type": "balance",
        "amount": 50
    },
    "balance_100": {
        "title": "100 дополнительных запросов",
        "description": "Пополнение баланса AI запросов",
        "price": 35,
        "type": "balance",
        "amount": 100
    },
    "subscription_month": {
        "title": "Подписка на 30 дней (безлимит)",
        "description": "Неограниченные запросы к ИИ на 30 дней",
        "price": 50,
        "type": "subscription",
        "days": 30
    }
}

@router.callback_query(lambda c: c.data == "donate")
async def donate_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = get_user(user_id)
    text = (
        "⭐ **Поддержать проект Telegram Stars**\n\n"
        "Вы можете приобрести:\n"
        "🎁 **10 запросов** – 5 ⭐\n"
        "🎁 **50 запросов** – 20 ⭐\n"
        "🎁 **100 запросов** – 35 ⭐\n"
        "👑 **Подписка на 30 дней (безлимит)** – 50 ⭐\n\n"
        "⭐ Как работают Telegram Stars?\n"
        "Это внутренняя валюта Telegram. Вы покупаете звёзды в приложении Telegram (iOS/Android/Desktop) и оплачиваете ими товары бота.\n\n"
        "Нажмите на кнопку с нужным товаром, чтобы оплатить."
    )
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="⭐ 10 запросов (5 ⭐)", callback_data="buy_balance_10")],
        [types.InlineKeyboardButton(text="⭐ 50 запросов (20 ⭐)", callback_data="buy_balance_50")],
        [types.InlineKeyboardButton(text="⭐ 100 запросов (35 ⭐)", callback_data="buy_balance_100")],
        [types.InlineKeyboardButton(text="👑 Подписка на месяц (50 ⭐)", callback_data="buy_subscription_month")],
        [types.InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("buy_"))
async def buy_product(callback: CallbackQuery):
    product_key = callback.data.replace("buy_", "")
    if product_key not in PRODUCTS:
        await callback.answer("Товар не найден", show_alert=True)
        return
    product = PRODUCTS[product_key]
    user_id = callback.from_user.id

    # Создаём счёт (invoice) через Telegram Stars
    prices = [LabeledPrice(label=product["title"], amount=product["price"])]
    await callback.bot.send_invoice(
        chat_id=user_id,
        title=product["title"],
        description=product["description"],
        payload=product_key,  # идентификатор товара
        provider_token="",    # для Stars не нужен
        currency="XTR",
        prices=prices,
        start_parameter=f"buy_{product_key}",
        need_name=False,
        need_phone_number=False,
        need_email=False,
        need_shipping_address=False,
        is_flexible=False
    )
    await callback.answer()

# Обработка предварительной проверки платежа (автоматически подтверждаем)
@router.pre_checkout_query(lambda query: True)
async def pre_checkout_query_handler(query: PreCheckoutQuery):
    await query.answer(ok=True)

# Обработка успешного платежа
@router.message(lambda m: m.successful_payment is not None)
async def successful_payment_handler(message: types.Message):
    payment = message.successful_payment
    user_id = message.from_user.id
    product_key = payment.invoice_payload
    telegram_payload = payment.telegram_payment_charge_id

    if product_key not in PRODUCTS:
        await message.answer("❌ Неизвестный товар. Обратитесь к администратору.")
        return

    product = PRODUCTS[product_key]
    
    # Записываем платёж в БД (для истории)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO payments (user_id, amount, currency, product, telegram_payload, completed)
        VALUES (?, ?, ?, ?, ?, 1)
    """, (user_id, product["price"], "XTR", product_key, telegram_payload))
    conn.commit()
    conn.close()

    user = get_user(user_id)

    # Начисляем товар
    if product["type"] == "balance":
        new_balance = user['balance_requests'] + product["amount"]
        update_user(user_id, balance_requests=new_balance)
        await message.answer(f"✅ Пополнение успешно!\nВам начислено **{product['amount']}** запросов.\nТеперь ваш баланс: **{new_balance}** запросов.")
    elif product["type"] == "subscription":
        days = product["days"]
        until = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        update_user(user_id, subscribed=1, subscription_until=until)
        await message.answer(f"✅ Подписка оформлена!\nДействует до **{until}**. Теперь у вас неограниченные запросы.")

    # Отправляем клавиатуру главного меню (чтобы продолжить)
    from keyboards import main_menu
    await message.answer("Вы можете продолжить пользоваться ботом:", reply_markup=main_menu(user_id))

# Альтернативная команда /donate (если нужно)
@router.message(Command("donate"))
async def cmd_donate(message: types.Message):
    user_id = message.from_user.id
    user = get_user(user_id)
    text = (
        "⭐ **Поддержать проект Telegram Stars**\n\n"
        "Вы можете приобрести:\n"
        "🎁 **10 запросов** – 5 ⭐\n"
        "🎁 **50 запросов** – 20 ⭐\n"
        "🎁 **100 запросов** – 35 ⭐\n"
        "👑 **Подписка на 30 дней (безлимит)** – 50 ⭐\n\n"
        "Нажмите на кнопку ниже, чтобы открыть меню покупок."
    )
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="💎 Купить звёзды", callback_data="donate")]
    ])
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
