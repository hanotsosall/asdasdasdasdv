import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict
import uvicorn
from database import get_user, update_user, add_history, clear_history
from utils.groq_client import ask_groq_with_history
from utils.openai_client import ask_openai_with_history
from utils.image_gen import generate_image

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

class ChatReq(BaseModel):
    model: str
    message: str
    user_id: int
    history: List[Dict[str, str]]

class ImageReq(BaseModel):
    prompt: str
    model: str
    user_id: int

class SetDefaultAI(BaseModel):
    user_id: int
    default_ai: str

class ClearHistoryReq(BaseModel):
    user_id: int

@app.post("/api/chat")
async def chat(req: ChatReq):
    if req.model not in ("groq", "openai"):
        return {"reply": "❌ Модель не поддерживается"}
    user = get_user(req.user_id)
    if user['balance_requests'] <= 0 and not user['subscribed']:
        return {"reply": "❌ Недостаточно запросов."}
    history = [(h['role'], h['content']) for h in req.history[-10:]]
    if req.model == "groq":
        answer = ask_groq_with_history(req.message, history)
    else:
        answer = ask_openai_with_history(req.message, history)
    add_history(req.user_id, req.model, "user", req.message)
    add_history(req.user_id, req.model, "assistant", answer)
    update_user(req.user_id, balance_requests=user['balance_requests']-1, total_requests=user['total_requests']+1)
    return {"reply": answer}

@app.post("/api/generate_image")
async def gen_image(req: ImageReq):
    url = await generate_image(req.prompt, req.model)
    if url:
        user = get_user(req.user_id)
        update_user(req.user_id, total_images=user['total_images']+1)
        return {"url": url}
    return {"error": "Ошибка генерации"}

@app.get("/api/profile")
async def profile(user_id: int):
    u = get_user(user_id)
    return {
        "user_id": u['user_id'],
        "balance_requests": u['balance_requests'],
        "ref_count": u['ref_count'],
        "subscribed": u['subscribed'],
        "total_requests": u['total_requests']
    }

@app.post("/api/set_default_ai")
async def set_default(req: SetDefaultAI):
    if req.default_ai not in ("groq", "openai"):
        return {"error": "Недопустимая модель"}
    update_user(req.user_id, default_ai=req.default_ai)
    return {"status": "ok"}

@app.get("/api/get_settings")
async def get_settings(user_id: int):
    u = get_user(user_id)
    default = u['default_ai']
    if default not in ("groq", "openai"):
        default = "groq"
        update_user(user_id, default_ai=default)
    return {"default_ai": default}

@app.post("/api/clear_history")
async def clear_history_endpoint(req: ClearHistoryReq):
    clear_history(req.user_id)
    return {"status": "ok"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
