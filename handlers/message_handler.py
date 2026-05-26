from aiogram import Router, types
from aiogram.filters import Text, Command, StateFilter
from aiogram.fsm.context import FSMContext
from database import get_user, update_user, add_history, get_history
from utils.groq_client import ask_groq_with_history
from utils.deepseek_client import ask_deepseek_with_history

router = Router()

@router.message(Text(), ~Command(commands=["start"]))
async def handle_default_ai(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        return

    user_id = message.from_user.id
    user = get_user(user_id)
    if user['balance_requests'] <= 0 and not user['subscribed']:
        await message.answer("❌ Закончились бесплатные запросы. Оформи подписку или пригласи друга.")
        return

    ai_name = user['default_ai']
    prompt = message.text
    await message.bot.send_chat_action(message.chat.id, "typing")
    history = get_history(user_id, ai_name, limit=10)
    try:
        if ai_name == "groq":
            answer = ask_groq_with_history(prompt, history)
        elif ai_name == "deepseek":
            answer = ask_deepseek_with_history(prompt, history)
        else:
            answer = "Неизвестная ИИ"
        add_history(user_id, ai_name, "user", prompt)
        add_history(user_id, ai_name, "assistant", answer)
        update_user(user_id,
                    balance_requests=user['balance_requests']-1,
                    total_requests=user['total_requests']+1)
        await message.answer(answer)
    except Exception as e:
        await message.answer(f"⚠️ Ошибка {ai_name}: {e}")
