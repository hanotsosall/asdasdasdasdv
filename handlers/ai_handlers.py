from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from database import get_user, update_user, add_history, get_history
from utils.groq_client import ask_groq_with_history
from utils.openai_client import ask_openai_with_history
from keyboards import back_button

router = Router()

class AIState(StatesGroup):
    waiting_groq = State()
    waiting_openai = State()

@router.callback_query(lambda c: c.data == "ai_groq")
async def ask_groq_menu(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🤖 Отправь запрос для Groq (LLaMA 3):", reply_markup=back_button())
    await state.set_state(AIState.waiting_groq)
    await callback.answer()

@router.callback_query(lambda c: c.data == "ai_openai")
async def ask_openai_menu(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🧠 Отправь запрос для OpenAI (GPT-3.5):", reply_markup=back_button())
    await state.set_state(AIState.waiting_openai)
    await callback.answer()

async def process_ai_message(message: Message, state: FSMContext, ai_name: str, api_func):
    user_id = message.from_user.id
    user = get_user(user_id)
    if user['balance_requests'] <= 0 and not user['subscribed']:
        await message.answer("❌ Закончились запросы. Оформи подписку или пригласи друга.")
        await state.clear()
        return
    history = get_history(user_id, ai_name, 10)
    prompt = message.text
    await message.bot.send_chat_action(message.chat.id, "typing")
    try:
        answer = api_func(prompt, history)
        add_history(user_id, ai_name, "user", prompt)
        add_history(user_id, ai_name, "assistant", answer)
        update_user(user_id, balance_requests=user['balance_requests']-1, total_requests=user['total_requests']+1)
        await message.answer(answer)
    except Exception as e:
        await message.answer(f"⚠️ Ошибка {ai_name}: {e}")
    await state.clear()

@router.message(AIState.waiting_groq)
async def handle_groq(message: Message, state: FSMContext):
    await process_ai_message(message, state, "groq", ask_groq_with_history)

@router.message(AIState.waiting_openai)
async def handle_openai(message: Message, state: FSMContext):
    await process_ai_message(message, state, "openai", ask_openai_with_history)
