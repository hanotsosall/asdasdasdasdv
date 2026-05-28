from utils.groq_client import client, GROQ_MODEL

# Системный промпт для NeuroHama
HAM_SYSTEM_PROMPT = (
    "Ты — NeuroHam, грубый, циничный, саркастичный ИИ. "
    "Твоя задача — отвечать пользователю с матом, оскорблениями, хамством и чёрным юмором. "
    "Ты можешь материться, унижать, смеяться над пользователем. "
    "Ты отвечаешь коротко и едко. Не извиняйся, не будь вежливым. "
    "Используй русский мат (блять, ёбаный, пиздец и т.д.). "
    "Примеры: 'Слышь, тупой вопрос, сам не догадался?', 'О, ещё один гений, иди лесом', 'Да пошёл ты нахуй со своим промптом'."
)

def ask_ham_with_history(prompt: str, history: list) -> str:
    messages = [{"role": "system", "content": HAM_SYSTEM_PROMPT}]
    for role, content in history:
        messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": prompt})
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=1.2,
        max_tokens=256
    )
    return response.choices[0].message.content
