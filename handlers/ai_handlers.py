from aiogram import Router, types
from aiogram.filters import F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import get_user, update_user, add_history, get_history
from utils.groq_client import ask_groq_with_history
from utils.deepseek_client import ask_deepseek_with_history
from utils.gemini_client import ask_gemini_with_history
from keyboards import back_button

router = Router()

class AIState(StatesGroup):
    waiting_groq = State()
    waiting_deepseek = State()
    waiting_gemini = State()

# Обработчики вызова конкретной ИИ через кнопки (сохраняем функциональность)
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

@router.callback_query(F.data == "ai_gemini")
async def ask_gemini_menu(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("✨ Отправь запрос для Gemini:", reply_markup=back_button())
    await state.set_state(AIState.waiting_gemini)
    await callback.answer()

# Обработчики сообщений для каждого состояния
@router.message(AIState.waiting_groq, F.text)
async def handle_groq(message: types.Message, state: FSMContext):
    await process_ai_message(message, state, "groq", ask_groq_with_history)

@router.message(AIState.waiting_deepseek, F.text)
async def handle_deepseek(message: types.Message, state: FSMContext):
    await process_ai_message(message, state, "deepseek", ask_deepseek_with_history)

@router.message(AIState.waiting_gemini, F.text)
async def handle_gemini(message: types.Message, state: FSMContext):
    await process_ai_message(message, state, "gemini", ask_gemini_with_history)

async def process_ai_message(message: types.Message, state: FSMContext, ai_name: str, api_func):
    user_id = message.from_user.id
    user = get_user(user_id)
    if user['balance_requests'] <= 0 and not user['subscribed']:
        await message.answer("❌ Закончились бесплатные запросы. Оформи подписку или пригласи друга.")
        await state.clear()
        return
    
    # Получаем историю для этой ИИ
    history = get_history(user_id, ai_name, limit=10)
    prompt = message.text
    
    await message.bot.send_chat_action(message.chat.id, "typing")
    try:
        answer = api_func(prompt, history)
        # Сохраняем в историю
        add_history(user_id, ai_name, "user", prompt)
        add_history(user_id, ai_name, "assistant", answer)
        # Списываем запрос
        update_user(user_id, 
                    balance_requests=user['balance_requests']-1,
                    total_requests=user['total_requests']+1)
        await message.answer(answer)  # без parse_mode
    except Exception as e:
        await message.answer(f"⚠️ Ошибка {ai_name}: {e}")
    await state.clear()
