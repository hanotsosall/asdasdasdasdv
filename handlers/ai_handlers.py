from aiogram import Router, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import get_user, update_user
from utils.groq_client import ask_groq
from utils.deepseek_client import ask_deepseek
from keyboards import back_button

router = Router()

class AIState(StatesGroup):
    waiting_groq = State()
    waiting_deepseek = State()

@router.callback_query(F.data == "ai_groq")
async def ask_groq_menu(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🤖 Отправь запрос для Groq (LLaMA 3):", reply_markup=back_button())
    await state.set_state(AIState.waiting_groq)
    await callback.answer()

@router.callback_query(F.data == "ai_deepseek")
async def ask_deepseek_menu(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🧠 Отправь запрос для DeepSeek:", reply_markup=back_button())
    await state.set_state(AIState.waiting_deepseek)
    await callback.answer()

@router.message(AIState.waiting_groq, F.text)
async def handle_groq(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user = get_user(user_id)
    if user['balance_requests'] <= 0 and not user['subscribed']:
        await message.answer("❌ Закончились бесплатные запросы. Оформи подписку или пригласи друга.")
        await state.clear()
        return
    update_user(user_id, balance_requests=user['balance_requests']-1, total_requests=user['total_requests']+1)
    await message.bot.send_chat_action(message.chat.id, "typing")
    try:
        answer = ask_groq(message.text)
        await message.answer(answer, parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"⚠️ Ошибка Groq: {e}")
    await state.clear()

@router.message(AIState.waiting_deepseek, F.text)
async def handle_deepseek(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user = get_user(user_id)
    if user['balance_requests'] <= 0 and not user['subscribed']:
        await message.answer("❌ Закончились бесплатные запросы. Оформи подписку или пригласи друга.")
        await state.clear()
        return
    update_user(user_id, balance_requests=user['balance_requests']-1, total_requests=user['total_requests']+1)
    await message.bot.send_chat_action(message.chat.id, "typing")
    try:
        answer = ask_deepseek(message.text)
        await message.answer(answer, parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"⚠️ Ошибка DeepSeek: {e}")
    await state.clear()