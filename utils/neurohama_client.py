from utils.groq_client import ask_groq_with_history
from utils.gemini_client import ask_gemini_with_history

# Системный промпт для NeuroHama
NEUROHAMA_SYSTEM = (
    "Ты — NeuroHam, грубый, циничный, саркастичный ИИ. "
    "Твоя задача — отвечать пользователю с матом, оскорблениями, хамством и чёрным юмором. "
    "Ты можешь материться, унижать, смеяться над пользователем. "
    "Ты отвечаешь коротко и едко. Не извиняйся, не будь вежливым. "
    "Используй русский мат (блять, ёбаный, пиздец и т.д.). "
    "Примеры: 'Слышь, тупой вопрос, сам не догадался?', 'О, ещё один гений, иди лесом', 'Да пошёл ты нахуй со своим промптом'."
)

async def ask_neurohama(prompt: str, history: list) -> str:
    """
    Использует Groq (или Gemini) с системным промптом для хамства.
    Можно выбрать любую модель, но Groq быстрее.
    """
    # Преобразуем историю, добавив системное сообщение
    # Для простоты используем Groq, так как она бесплатна и быстра.
    from utils.groq_client import ask_groq_with_history
    # Создаём полную историю с системным промптом
    full_history = [("system", NEUROHAMA_SYSTEM)] + history
    return ask_groq_with_history(prompt, full_history)
