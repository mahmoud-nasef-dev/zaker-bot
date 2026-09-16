import sqlite3
from datetime import date, datetime, timedelta
from config import (
    FREE_DAILY_LIMIT, PREMIUM_DAILY_LIMIT, ADMIN_DAILY_LIMIT,
    ADMIN_IDS, DATABASE_FILE
)


# ===== نظام النقاط =====
POINTS_REWARDS = {
    "text_analysis": 5,       # تحليل نص
    "pdf_analysis": 10,       # تحليل PDF
    "quiz_complete": 15,      # إكمال كويز
    "daily_gift": 5,          # هدية يومية
    "invite_friend": 20,      # دعوة صديق
    "streak_bonus_7": 50,     # 7 أيام متتالية
    "streak_bonus_30": 500,   # 30 يوم متتالي
}

# ===== المستويات =====
LEVELS = [
    {"level": 1, "name": "🌱 مبتدئ", "min_points": 0, "max_points": 100},
    {"level": 2, "name": "📚 طالب", "min_points": 100, "max_points": 500},
    {"level": 3, "name": "⭐ شاطر", "min_points": 500, "max_points": 2000},
    {"level": 4, "name": "🏆 متفوق", "min_points": 2000, "max_points": 5000},
    {"level": 5, "name": "💎 عبقري", "min_points": 5000, "max_points": 10000},
    {"level": 6, "name": "👑 أسطورة", "min_points": 10000, "max_points": 999999},
]


def get_level_info(points):
    """بيرجع معلومات المستوى حسب النقاط"""
    for level in LEVELS:
        if level["min_points"] <= points < level["max_points"]:
            return level
    return LEVELS[-1]


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
            plan TEXT DEFAULT 'free',
            points INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            daily_streak INTEGER DEFAULT 0,
            last_daily_claim TEXT,
            invited_by INTEGER DEFAULT NULL,
            invited_count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def get_or_create_user(user_id, username, first_name, invited_by=None):
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
            INSERT INTO users 
            (user_id, username, first_name, joined_date, last_used, plan, invited_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, username, first_name, today, today, plan, invited_by))
        conn.commit()

        # لو في دعوة، نكافئ الداعي
        if invited_by:
            add_points(invited_by, POINTS_REWARDS["invite_friend"])
            cursor.execute("""
                UPDATE users SET invited_count = invited_count + 1
                WHERE user_id = ?
            """, (invited_by,))
            conn.commit()

        conn.close()
        return {
            "user_id": user_id, "plan": plan, "daily_requests": 0,
            "total_requests": 0, "points": 0, "level": 1,
            "daily_streak": 0, "is_new": True
        }

    # مستخدم موجود
    last_used = user[4]
    daily_requests = user[6]

    if last_used != today:
        cursor.execute("""
            UPDATE users SET daily_requests = 0, last_used = ? WHERE user_id = ?
        """, (today, user_id))
        daily_requests = 0

    conn.commit()
    conn.close()

    return {
        "user_id": user[0], "plan": user[7], "daily_requests": daily_requests,
        "total_requests": user[5], "points": user[8], "level": user[9],
        "daily_streak": user[10], "is_new": False
    }


def add_points(user_id, amount):
    """بيضيف نقاط للمستخدم"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users SET points = points + ? WHERE user_id = ?
    """, (amount, user_id))

    # نحدث المستوى
    cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        new_points = row[0]
        level_info = get_level_info(new_points)
        cursor.execute("""
            UPDATE users SET level = ? WHERE user_id = ?
        """, (level_info["level"], user_id))

    conn.commit()
    conn.close()


def get_user_points(user_id):
    """بيرجع نقاط المستخدم"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT points, level FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0], row[1]
    return 0, 1


def claim_daily_gift(user_id):
    """بيحاول يستلم الهدية اليومية"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT last_daily_claim, daily_streak FROM users WHERE user_id = ?
    """, (user_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return {"success": False, "message": "المستخدم مش موجود"}

    last_claim, streak = row
    now = datetime.now()

    if last_claim:
        last_claim_date = datetime.strptime(last_claim, "%Y-%m-%d %H:%M:%S")
        diff = now - last_claim_date

        if diff < timedelta(hours=24):
            remaining = timedelta(hours=24) - diff
            hours = remaining.seconds // 3600
            minutes = (remaining.seconds % 3600) // 60
            conn.close()
            return {
                "success": False,
                "message": f"⏳ استنى {hours} ساعة و {minutes} دقيقة",
                "remaining_hours": hours,
            }

        # لو الفرقة أكتر من 48 ساعة، نصفّر السلسلة
        if diff > timedelta(hours=48):
            streak = 0
        else:
            streak += 1
    else:
        streak = 1

    # نحسب النقاط
    points = POINTS_REWARDS["daily_gift"]
    bonus = 0

    if streak == 7:
        bonus = POINTS_REWARDS["streak_bonus_7"]
    elif streak == 30:
        bonus = POINTS_REWARDS["streak_bonus_30"]

    total = points + bonus

    # نحدث المستخدم
    cursor.execute("""
        UPDATE users 
        SET last_daily_claim = ?, daily_streak = ?, points = points + ?
        WHERE user_id = ?
    """, (now.strftime("%Y-%m-%d %H:%M:%S"), streak, total, user_id))

    # نحدث المستوى
    cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    new_points = cursor.fetchone()[0]
    level_info = get_level_info(new_points)
    cursor.execute("UPDATE users SET level = ? WHERE user_id = ?",
                   (level_info["level"], user_id))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "points": points,
        "bonus": bonus,
        "total": total,
        "streak": streak,
        "new_points": new_points,
        "level": level_info,
    }


def get_daily_status(user_id):
    """بيرجع حالة الهدية اليومية"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT last_daily_claim, daily_streak FROM users WHERE user_id = ?
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {"can_claim": True, "streak": 0, "remaining_hours": 0}

    last_claim, streak = row

    if not last_claim:
        return {"can_claim": True, "streak": 0, "remaining_hours": 0}

    last_claim_date = datetime.strptime(last_claim, "%Y-%m-%d %H:%M:%S")
    diff = datetime.now() - last_claim_date

    if diff >= timedelta(hours=24):
        # لو الفرقة أكتر من 48 ساعة، السلسلة اتكسرت
        if diff > timedelta(hours=48):
            streak = 0
        return {"can_claim": True, "streak": streak, "remaining_hours": 0}

    remaining = timedelta(hours=24) - diff
    hours = remaining.seconds // 3600
    return {"can_claim": False, "streak": streak, "remaining_hours": hours}


def get_leaderboard(limit=10):
    """بيرجع أعلى 10 مستخدمين"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_id, first_name, username, points, level
        FROM users
        ORDER BY points DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def increment_usage(user_id, points=0):
    """بيزود عدد الاستخدامات + النقاط"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users
        SET total_requests = total_requests + 1,
            daily_requests = daily_requests + 1,
            points = points + ?
        WHERE user_id = ?
    """, (points, user_id))

    # نحدث المستوى
    cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        level_info = get_level_info(row[0])
        cursor.execute("UPDATE users SET level = ? WHERE user_id = ?",
                       (level_info["level"], user_id))

    conn.commit()
    conn.close()


def check_limit(user_id):
    """بيتأكد إن المستخدم لسه عنده استخدامات متاحة"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT plan, daily_requests, points FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return True, 0

    plan, daily_requests, points = row

    limits = {
        "free": FREE_DAILY_LIMIT,
        "premium": PREMIUM_DAILY_LIMIT,
        "admin": ADMIN_DAILY_LIMIT,
    }

    limit = limits.get(plan, FREE_DAILY_LIMIT)

    # مكافأة: لو المستخدم في مستوى أعلى، نزود الحد
    level_info = get_level_info(points)
    bonus = (level_info["level"] - 1) * 2  # كل مستوى = +2 استخدام
    limit += bonus

    if daily_requests >= limit:
        return False, 0

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

    cursor.execute("SELECT SUM(points) FROM users")
    total_points = cursor.fetchone()[0] or 0

    conn.close()

    return {
        "total_users": total_users,
        "premium_users": premium_users,
        "total_requests": total_requests,
        "total_points": total_points,
    }

def get_all_users(limit=20):
    """بيرجع آخر 20 مستخدم"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_id, first_name, username, points, level, plan, last_used
        FROM users
        ORDER BY last_used DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_user_details(user_id):
    """بيرجع تفاصيل مستخدم معين"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_id, first_name, username, joined_date, last_used,
               total_requests, points, level, plan, daily_streak, invited_count
        FROM users WHERE user_id = ?
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def get_detailed_stats():
    """إحصائيات مفصلة"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    today = str(date.today())
    cursor.execute("SELECT COUNT(*) FROM users WHERE last_used = ?", (today,))
    active_today = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE plan = 'premium'")
    premium_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE plan = 'admin'")
    admin_users = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(total_requests) FROM users")
    total_requests = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(points) FROM users")
    total_points = cursor.fetchone()[0] or 0

    # أعلى 5 مستخدمين
    cursor.execute("""
        SELECT first_name, points FROM users
        ORDER BY points DESC LIMIT 5
    """)
    top_users = cursor.fetchall()

    conn.close()

    return {
        "total_users": total_users,
        "active_today": active_today,
        "premium_users": premium_users,
        "admin_users": admin_users,
        "total_requests": total_requests,
        "total_points": total_points,
        "top_users": top_users,
    }


def ban_user(user_id):
    """حظر مستخدم (بيغير الخطة لـ banned)"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET plan = 'banned' WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def unban_user(user_id):
    """فك الحظر"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET plan = 'free' WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def get_all_user_ids():
    """بيرجع كل الـ user_ids (للبث)"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE plan != 'banned'")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]
def get_all_users(limit=20):
    """بيرجع آخر 20 مستخدم"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_id, first_name, username, points, level, plan, last_used
        FROM users
        ORDER BY last_used DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows