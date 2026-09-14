import sqlite3
from datetime import date
from config import FREE_DAILY_LIMIT, PREMIUM_DAILY_LIMIT, ADMIN_DAILY_LIMIT, ADMIN_IDS, DATABASE_FILE


def init_db():
    """بيبدأ قاعدة البيانات لو مش موجودة"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            joined_date TEXT,
            last_used TEXT,
            total_requests INTEGER DEFAULT 0,
            daily_requests INTEGER DEFAULT 0,
            plan TEXT DEFAULT 'free'
        )
    """)
    conn.commit()
    conn.close()


def get_or_create_user(user_id, username, first_name):
    """بيجيب المستخدم أو بيعمله واحد جديد"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    today = str(date.today())

    if user is None:
        # مستخدم جديد
        plan = "admin" if user_id in ADMIN_IDS else "free"
        cursor.execute("""
            INSERT INTO users (user_id, username, first_name, joined_date, last_used, plan)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, username, first_name, today, today, plan))
        conn.commit()
        conn.close()
        return {"user_id": user_id, "plan": plan, "daily_requests": 0, "total_requests": 0}

    # مستخدم موجود - نتأكد من آخر استخدام
    last_used = user[4]
    daily_requests = user[6]

    if last_used != today:
        # يوم جديد - نصفّر العداد
        cursor.execute("""
            UPDATE users SET daily_requests = 0, last_used = ? WHERE user_id = ?
        """, (today, user_id))
        daily_requests = 0

    conn.commit()
    conn.close()

    return {
        "user_id": user[0],
        "plan": user[7],
        "daily_requests": daily_requests,
        "total_requests": user[5],
    }


def increment_usage(user_id):
    """بيزود عدد الاستخدامات"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users
        SET total_requests = total_requests + 1,
            daily_requests = daily_requests + 1
        WHERE user_id = ?
    """, (user_id,))
    conn.commit()
    conn.close()


def check_limit(user_id):
    """بيتأكد إن المستخدم لسه عنده استخدامات متاحة"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT plan, daily_requests FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return True, 0

    plan, daily_requests = row

    limits = {
        "free": FREE_DAILY_LIMIT,
        "premium": PREMIUM_DAILY_LIMIT,
        "admin": ADMIN_DAILY_LIMIT,
    }

    limit = limits.get(plan, FREE_DAILY_LIMIT)

    if daily_requests >= limit:
        return False, limit - daily_requests

    return True, limit - daily_requests


def get_user_plan(user_id):
    """بيرجع خطة المستخدم"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT plan FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else "free"


def set_user_plan(user_id, plan):
    """بيغير خطة المستخدم (للأدمن)"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET plan = ? WHERE user_id = ?", (plan, user_id))
    conn.commit()
    conn.close()


def get_stats():
    """إحصائيات عامة للأدمن"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE plan = 'premium'")
    premium_users = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(total_requests) FROM users")
    total_requests = cursor.fetchone()[0] or 0

    conn.close()

    return {
        "total_users": total_users,
        "premium_users": premium_users,
        "total_requests": total_requests,
    }