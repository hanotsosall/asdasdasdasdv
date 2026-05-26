import sqlite3
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
            reg_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    columns = ["user_id", "username", "first_name", "balance_requests", "subscribed", "subscription_until",
               "ref_count", "ref_by", "total_requests", "total_images", "reg_date"]
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