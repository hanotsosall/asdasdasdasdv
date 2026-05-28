import sqlite3
from datetime import datetime
import shutil
import os
from datetime import datetime

DB_PATH = "bot_database.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            balance_requests INTEGER DEFAULT 10,
            subscribed BOOLEAN DEFAULT 0,
            subscription_until TIMESTAMP,
            ref_count INTEGER DEFAULT 0,
            ref_by INTEGER,
            total_requests INTEGER DEFAULT 0,
            total_images INTEGER DEFAULT 0,
            reg_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            default_ai TEXT DEFAULT 'groq',
            image_model TEXT DEFAULT 'pollinations'
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS referrals (
            referrer_id INTEGER,
            referred_id INTEGER PRIMARY KEY,
            reward_claimed BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            currency TEXT,
            product TEXT,
            telegram_payload TEXT,
            completed BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            ai_name TEXT,
            role TEXT,
            content TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS banned_users (
            user_id INTEGER PRIMARY KEY,
            reason TEXT,
            banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS required_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id INTEGER UNIQUE,
            channel_username TEXT,
            channel_link TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def get_user(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
    conn.close()
    columns = ["user_id", "username", "first_name", "balance_requests",
               "subscribed", "subscription_until", "ref_count", "ref_by",
               "total_requests", "total_images", "reg_date", "default_ai", "image_model"]
    return dict(zip(columns, row))

def update_user(user_id: int, **kwargs):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    set_clause = ", ".join([f"{k}=?" for k in kwargs.keys()])
    values = list(kwargs.values()) + [user_id]
    c.execute(f"UPDATE users SET {set_clause} WHERE user_id = ?", values)
    conn.commit()
    conn.close()

def add_referral(referrer_id: int, referred_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO referrals (referrer_id, referred_id) VALUES (?, ?)", (referrer_id, referred_id))
        c.execute("UPDATE users SET balance_requests = balance_requests + 5, ref_count = ref_count + 1 WHERE user_id = ?", (referrer_id,))
        conn.commit()
    except:
        pass
    conn.close()

def add_history(user_id: int, ai_name: str, role: str, content: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO chat_history (user_id, ai_name, role, content) VALUES (?, ?, ?, ?)",
              (user_id, ai_name, role, content))
    conn.commit()
    conn.close()

def get_history(user_id: int, ai_name: str, limit: int = 10) -> list:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT role, content FROM chat_history WHERE user_id = ? AND ai_name = ? ORDER BY timestamp DESC LIMIT ?",
              (user_id, ai_name, limit))
    rows = c.fetchall()
    conn.close()
    return list(reversed(rows))

def clear_history(user_id: int, ai_name: str = None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if ai_name:
        c.execute("DELETE FROM chat_history WHERE user_id = ? AND ai_name = ?", (user_id, ai_name))
    else:
        c.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def get_all_users(limit: int, offset: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT user_id, username, first_name, balance_requests, subscribed, total_requests FROM users LIMIT ? OFFSET ?", (limit, offset))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def count_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    count = c.fetchone()[0]
    conn.close()
    return count

def is_user_banned(user_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT 1 FROM banned_users WHERE user_id = ?", (user_id,))
    banned = c.fetchone() is not None
    conn.close()
    return banned

def ban_user(user_id: int, reason: str = ""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO banned_users (user_id, reason) VALUES (?, ?)", (user_id, reason))
    conn.commit()
    conn.close()

def unban_user(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM banned_users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def add_required_channel(channel_id: int, channel_username: str, channel_link: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO required_channels (channel_id, channel_username, channel_link) VALUES (?, ?, ?)",
              (channel_id, channel_username, channel_link))
    conn.commit()
    conn.close()

def remove_required_channel(channel_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM required_channels WHERE channel_id = ?", (channel_id,))
    conn.commit()
    conn.close()

def get_required_channels():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT channel_id, channel_username, channel_link FROM required_channels")
    rows = c.fetchall()
    conn.close()
    return [{"id": row[0], "username": row[1], "link": row[2]} for row in rows]

def is_channel_required(channel_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT 1 FROM required_channels WHERE channel_id = ?", (channel_id,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

async def ensure_default_channel(bot, username: str = "UltimateAI_info"):
    """Автоматически добавляет канал в обязательные, если его ещё нет."""
    from database import add_required_channel, get_required_channels
    channels = get_required_channels()
    # Проверяем, не добавлен ли уже канал с таким username
    for ch in channels:
        if ch['username'] == username:
            return
    try:
        chat = await bot.get_chat(f"@{username}")
        channel_id = chat.id
        channel_link = f"https://t.me/{username}"
        add_required_channel(channel_id, username, channel_link)
        print(f"✅ Канал @{username} добавлен в обязательные для подписки (ID: {channel_id})")
    except Exception as e:
        print(f"❌ Не удалось добавить канал @{username}: {e}")

def backup_database() -> str:
    """Создаёт копию текущей БД в папку backups/ с датой в имени."""
    if not os.path.exists("backups"):
        os.makedirs("backups")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{timestamp}.db"
    backup_path = os.path.join("backups", backup_name)
    shutil.copy2(DB_PATH, backup_path)
    return backup_path

def get_backup_list() -> list:
    """Возвращает список доступных бэкапов (имя файла, путь)."""
    if not os.path.exists("backups"):
        return []
    backups = []
    for f in os.listdir("backups"):
        if f.endswith(".db"):
            full_path = os.path.join("backups", f)
            size = os.path.getsize(full_path)
            backups.append({"name": f, "path": full_path, "size": size, "date": f.replace("backup_", "").replace(".db", "")})
    # сортируем по дате (новые сверху)
    backups.sort(key=lambda x: x["date"], reverse=True)
    return backups

def restore_database(backup_path: str) -> bool:
    """Восстанавливает БД из указанного бэкапа."""
    try:
        shutil.copy2(backup_path, DB_PATH)
        return True
    except Exception as e:
        print(f"Restore error: {e}")
        return False
