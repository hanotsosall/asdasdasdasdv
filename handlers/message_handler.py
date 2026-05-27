from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from database import get_user, update_user, add_history, get_history, is_user_banned
from utils.groq_client import ask_groq_with_history
from utils.gemini_client import ask_gemini_with_history
from utils.markdown_helper import markdown_to_html

router = Router()

@router.message(lambda m: m.text and not m.text.startswith('/'))
async def handle_default_ai(message: Message, state: FSMContext):
    if await state.get_state() is not None:
        return
    user_id = message.from_user.id
    if is_user_banned(user_id):
        await message.answer("⛔ Вы забанены.")
        return
    user = get_user(user_id)
    if user['balance_requests'] <= 0 and not user['subscribed']:
        await message.answer("❌ Недостаточно запросов.")
        return
    ai_name = user['default_ai']
    if ai_name not in ("groq", "gemini"):
        ai_name = "groq"
    history = get_history(user_id, ai_name, 10)
    await message.bot.send_chat_action(message.chat.id, "typing")
    try:
        if ai_name == "groq":
            answer = ask_groq_with_history(message.text, history)
        else:
            answer = ask_gemini_with_history(message.text, history)
        answer_html = markdown_to_html(answer)
        add_history(user_id, ai_name, "user", message.text)
        add_history(user_id, ai_name, "assistant", answer)
        update_user(user_id, balance_requests=user['balance_requests']-1, total_requests=user['total_requests']+1)
        await message.answer(answer_html, parse_mode="HTML")
    except Exception as e:
        await message.answer(f"⚠️ Ошибка: {e}", parse_mode="HTML")
