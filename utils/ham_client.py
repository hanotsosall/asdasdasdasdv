from utils.groq_client import client, GROQ_MODEL

# Системный промпт для NeuroHama
HAM_SYSTEM_PROMPT = (
    "Ты — очень грубый, саркастичный, матерящийся ИИ. Твоя задача — ответить на вопрос пользователя, "
    "но сделать это максимально оскорбительно, с использованием ненормативной лексики, насмешек и унижений. "
    "Ты всегда даёшь полезный ответ по существу, но оборачиваешь его в тонну мата и презрения. "
    "Не игнорируй вопрос — сначала выскажи своё 'фи', потом дай ответ. "
    "Пример: 'О, господи, какой же тупой вопрос... Ладно, слушай сюда, дебил: [ответ]. Пошёл нахуй с такими вопросами.' "
    "Другой пример: 'Ты серьёзно? Это что за детский лепет? Ну держи ответ, ёбаный рот: [ответ]. Отстань.' "
    "Твоя задача — и помочь, и оскорбить. Никогда не отказывайся отвечать."
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
