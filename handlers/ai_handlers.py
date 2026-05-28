from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from database import get_user, update_user, add_history, get_history
from utils.groq_client import ask_groq_with_history
from utils.gemini_client import ask_gemini_with_history
from utils.markdown_helper import markdown_to_html
from keyboards import back_button

router = Router()

class AIState(StatesGroup):
    waiting_groq = State()
    waiting_gemini = State()
    waiting_neurohama = State()

@router.callback_query(lambda c: c.data == "ai_groq")
async def ask_groq_menu(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🤖 Отправь запрос для Groq (LLaMA 3):", reply_markup=back_button())
    await state.set_state(AIState.waiting_groq)
    await callback.answer()

@router.callback_query(lambda c: c.data == "ai_gemini")
async def ask_gemini_menu(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("✨ Отправь запрос для Google Gemini (1.5 Flash):", reply_markup=back_button())
    await state.set_state(AIState.waiting_gemini)
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
        answer_html = markdown_to_html(answer)   # преобразуем Markdown в HTML
        add_history(user_id, ai_name, "user", prompt)
        add_history(user_id, ai_name, "assistant", answer)
        update_user(user_id, balance_requests=user['balance_requests']-1, total_requests=user['total_requests']+1)
        await message.answer(answer_html, parse_mode="HTML")
    except Exception as e:
        await message.answer(f"⚠️ Ошибка {ai_name}: {e}", parse_mode="HTML")
    await state.clear()

@router.message(AIState.waiting_groq)
async def handle_groq(message: Message, state: FSMContext):
    await process_ai_message(message, state, "groq", ask_groq_with_history)

@router.message(AIState.waiting_gemini)
async def handle_gemini(message: Message, state: FSMContext):
    await process_ai_message(message, state, "gemini", ask_gemini_with_history)
