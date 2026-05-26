from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn
from database import get_user, update_user, add_history, get_history, clear_history
from utils.groq_client import ask_groq_with_history
from utils.deepseek_client import ask_deepseek_with_history
from utils.gemini_client import ask_gemini_with_history
from utils.image_gen import generate_image

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class ChatRequest(BaseModel):
    model: str
    message: str
    user_id: int
    history: List[Dict[str, str]]   # [{"role":"user","content":"..."}]

class ImageRequest(BaseModel):
    prompt: str
    model: str
    user_id: int

class SetDefaultAI(BaseModel):
    user_id: int
    default_ai: str

@app.post("/api/chat")
async def chat(req: ChatRequest):
    user = get_user(req.user_id)
    if user['balance_requests'] <= 0 and not user['subscribed']:
        return {"reply": "❌ Недостаточно запросов. Оформи подписку или пригласи друга."}
    
    # формируем историю из предыдущих сообщений + новое
    full_history = []
    for msg in req.history[-10:]:
        full_history.append((msg['role'], msg['content']))
    full_history.append(('user', req.message))
    
    if req.model == "groq":
        answer = ask_groq_with_history(req.message, full_history[:-1])  # без последнего пользовательского
    elif req.model == "deepseek":
        answer = ask_deepseek_with_history(req.message, full_history[:-1])
    elif req.model == "gemini":
        answer = ask_gemini_with_history(req.message, full_history[:-1])
    else:
        answer = "Неизвестная модель"
    
    # сохраняем сообщения в БД
    add_history(req.user_id, req.model, "user", req.message)
    add_history(req.user_id, req.model, "assistant", answer)
    # списываем запрос
    update_user(req.user_id, balance_requests=user['balance_requests']-1, total_requests=user['total_requests']+1)
    return {"reply": answer}

@app.post("/api/generate_image")
async def generate_image_endpoint(req: ImageRequest):
    url = await generate_image(req.prompt, req.model)
    if url:
        user = get_user(req.user_id)
        update_user(req.user_id, total_images=user['total_images']+1)
        return {"url": url}
    else:
        return {"error": "Генерация не удалась"}

@app.get("/api/profile")
async def profile(user_id: int):
    user = get_user(user_id)
    return {
        "user_id": user['user_id'],
        "balance_requests": user['balance_requests'],
        "ref_count": user['ref_count'],
        "subscribed": user['subscribed'],
        "total_requests": user['total_requests']
    }

@app.post("/api/set_default_ai")
async def set_default_ai(req: SetDefaultAI):
    update_user(req.user_id, default_ai=req.default_ai)
    return {"status": "ok"}

@app.get("/api/get_settings")
async def get_settings(user_id: int):
    user = get_user(user_id)
    return {"default_ai": user['default_ai']}

@app.post("/api/clear_history")
async def clear_history_endpoint(user_id: int):
    clear_history(user_id)
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
