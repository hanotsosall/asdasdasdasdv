from aiogram import Router, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from database import get_user, update_user, add_history, get_history
from utils.groq_client import ask_groq_with_history
from utils.deepseek_client import ask_deepseek_with_history
from utils.gemini_client import ask_gemini_with_history
import asyncio

router = Router()

@router.message(F.text & ~F.text.startswith('/'))
async def handle_default_ai(message: types.Message, state: FSMContext):
    # проверяем, не находится ли пользователь в каком-либо FSM состоянии (например, ожидание ответа от кнопок)
    current_state = await state.get_state()
    if current_state is not None:
        # если пользователь в диалоге с конкретной ИИ через кнопку, не перебиваем
        return

    user_id = message.from_user.id
    user = get_user(user_id)
    
    # проверка баланса
    if user['balance_requests'] <= 0 and not user['subscribed']:
        await message.answer("❌ Закончились бесплатные запросы. Оформи подписку или пригласи друга.")
        return

    ai_name = user['default_ai']
    prompt = message.text

    # Отправляем "печатает"
    await message.bot.send_chat_action(message.chat.id, "typing")
    
    # Получаем историю (последние 10 сообщений)
    history = get_history(user_id, ai_name, limit=10)
    
    try:
        if ai_name == "groq":
            answer = ask_groq_with_history(prompt, history)
        elif ai_name == "deepseek":
            answer = ask_deepseek_with_history(prompt, history)
        elif ai_name == "gemini":
            answer = ask_gemini_with_history(prompt, history)
        else:
            answer = "❌ Неизвестная ИИ"
        
        # Сохраняем в историю
        add_history(user_id, ai_name, "user", prompt)
        add_history(user_id, ai_name, "assistant", answer)
        
        # Списываем запрос
        update_user(user_id, 
                    balance_requests=user['balance_requests']-1,
                    total_requests=user['total_requests']+1)
        
        # Отправляем ответ (без parse_mode, чтобы избежать ошибок)
        await message.answer(answer)
    except Exception as e:
        await message.answer(f"⚠️ Ошибка {ai_name}: {e}")
