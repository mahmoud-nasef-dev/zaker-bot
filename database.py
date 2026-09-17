import os
import sqlite3
from datetime import date, datetime, timedelta
from config import (
    FREE_DAILY_LIMIT, PREMIUM_DAILY_LIMIT, ADMIN_DAILY_LIMIT,
    ADMIN_IDS, DATABASE_FILE
)

# ===== اكتشاف نوع قاعدة البيانات =====
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    import psycopg2
    USE_POSTGRES = True
    print("✅ باستخدام PostgreSQL")
else:
    USE_POSTGRES = False
    print("✅ باستخدام SQLite")


# ===== دوال مساعدة =====
def get_connection():
    if USE_POSTGRES:
        return psycopg2.connect(DATABASE_URL)
    else:
        return sqlite3.connect(DATABASE_FILE)


def placeholder():
    return "%s" if USE_POSTGRES else "?"


# ===== نظام النقاط =====
POINTS_REWARDS = {
    "text_analysis": 5,
    "pdf_analysis": 10,
    "quiz_complete": 15,
    "daily_gift": 5,
    "invite_friend": 20,
    "streak_bonus_7": 50,
    "streak_bonus_30": 500,
    "analysis_done": 30,
    "pomodoro_session": 20,
    "pomodoro_4_sessions": 50,
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
    for level in LEVELS:
        if level["min_points"] <= points < level["max_points"]:
            return level
    return LEVELS[-1]


# ===== إنشاء قاعدة البيانات =====
def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # ===== جدول users =====
    if USE_POSTGRES:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
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
                invited_by BIGINT DEFAULT NULL,
                invited_count INTEGER DEFAULT 0,
                college TEXT DEFAULT NULL,
                onboarding_done INTEGER DEFAULT 0
            )
        """)
    else:
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
                invited_count INTEGER DEFAULT 0,
                college TEXT DEFAULT NULL,
                onboarding_done INTEGER DEFAULT 0
            )
        """)

    conn.commit()

    # ===== Migration =====
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN college TEXT DEFAULT NULL")
        conn.commit()
    except:
        conn.rollback()

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN onboarding_done INTEGER DEFAULT 0")
        conn.commit()
    except:
        conn.rollback()

    # ===== جدول user_subjects =====
    if USE_POSTGRES:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_subjects (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                subject_name TEXT NOT NULL,
                added_date TEXT,
                is_active INTEGER DEFAULT 1
            )
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subject_name TEXT NOT NULL,
                added_date TEXT,
                is_active INTEGER DEFAULT 1
            )
        """)

    # ===== جدول user_analysis =====
    if USE_POSTGRES:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_analysis (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT UNIQUE NOT NULL,
                study_time TEXT,
                focus_duration TEXT,
                learning_style TEXT,
                hard_subject TEXT,
                goal TEXT,
                exam_timing TEXT,
                analysis_result TEXT,
                analysis_date TEXT
            )
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                study_time TEXT,
                focus_duration TEXT,
                learning_style TEXT,
                hard_subject TEXT,
                goal TEXT,
                exam_timing TEXT,
                analysis_result TEXT,
                analysis_date TEXT
            )
        """)

    # ===== جدول study_plans (جديد) =====
    if USE_POSTGRES:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS study_plans (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT UNIQUE NOT NULL,
                plan_text TEXT,
                plan_json TEXT,
                created_date TEXT,
                updated_date TEXT
            )
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS study_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                plan_text TEXT,
                plan_json TEXT,
                created_date TEXT,
                updated_date TEXT
            )
        """)

    # ===== جدول pomodoro_sessions (جديد) =====
    if USE_POSTGRES:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pomodoro_sessions (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                subject TEXT,
                duration INTEGER,
                session_date TEXT
            )
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pomodoro_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subject TEXT,
                duration INTEGER,
                session_date TEXT
            )
        """)

    conn.commit()
    cursor.close()
    conn.close()


# ===== دوال المستخدمين =====
def get_or_create_user(user_id, username, first_name, invited_by=None):
    conn = get_connection()
    cursor = conn.cursor()

    today = str(date.today())
    ph = placeholder()

    cursor.execute(
        f"SELECT * FROM users WHERE user_id = {ph}",
        (user_id,)
    )
    user = cursor.fetchone()

    if user is None:
        plan = "admin" if user_id in ADMIN_IDS else "free"
        cursor.execute(
            f"""INSERT INTO users 
                (user_id, username, first_name, joined_date, last_used, plan, invited_by)
                VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})""",
            (user_id, username, first_name, today, today, plan, invited_by)
        )
        conn.commit()

        if invited_by:
            cursor.execute(
                f"UPDATE users SET points = points + {ph} WHERE user_id = {ph}",
                (POINTS_REWARDS["invite_friend"], invited_by)
            )
            cursor.execute(
                f"UPDATE users SET invited_count = invited_count + 1 WHERE user_id = {ph}",
                (invited_by,)
            )
            conn.commit()

        cursor.close()
        conn.close()
        return {
            "user_id": user_id, "plan": plan, "daily_requests": 0,
            "total_requests": 0, "points": 0, "level": 1,
            "daily_streak": 0, "is_new": True, "onboarding_done": False
        }

    last_used = user[4]
    daily_requests = user[6]

    if last_used != today:
        cursor.execute(
            f"UPDATE users SET daily_requests = 0, last_used = {ph} WHERE user_id = {ph}",
            (today, user_id)
        )
        daily_requests = 0

    conn.commit()
    cursor.close()
    conn.close()

    onboarding = False
    if len(user) > 15:
        onboarding = bool(user[15])

    return {
        "user_id": user[0], "plan": user[7], "daily_requests": daily_requests,
        "total_requests": user[5], "points": user[8], "level": user[9],
        "daily_streak": user[10], "is_new": False, "onboarding_done": onboarding
    }


def complete_onboarding(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    cursor.execute(
        f"UPDATE users SET onboarding_done = 1 WHERE user_id = {ph}",
        (user_id,)
    )
    conn.commit()
    cursor.close()
    conn.close()


def set_user_college(user_id, college):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    cursor.execute(
        f"UPDATE users SET college = {ph} WHERE user_id = {ph}",
        (college, user_id)
    )
    conn.commit()
    cursor.close()
    conn.close()


def get_user_college(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"SELECT college FROM users WHERE user_id = {ph}",
            (user_id,)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row[0] if row and row[0] else None
    except Exception as e:
        cursor.close()
        conn.close()
        print(f"⚠️ خطأ في get_user_college: {e}")
        return None


# ===== دوال النقاط =====
def add_points(user_id, amount):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    cursor.execute(
        f"UPDATE users SET points = points + {ph} WHERE user_id = {ph}",
        (amount, user_id)
    )

    cursor.execute(
        f"SELECT points FROM users WHERE user_id = {ph}",
        (user_id,)
    )
    row = cursor.fetchone()
    if row:
        level_info = get_level_info(row[0])
        cursor.execute(
            f"UPDATE users SET level = {ph} WHERE user_id = {ph}",
            (level_info["level"], user_id)
        )

    conn.commit()
    cursor.close()
    conn.close()


def get_user_points(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    cursor.execute(
        f"SELECT points, level FROM users WHERE user_id = {ph}",
        (user_id,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row:
        return row[0], row[1]
    return 0, 1


def increment_usage(user_id, points=0):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    cursor.execute(
        f"""UPDATE users
            SET total_requests = total_requests + 1,
                daily_requests = daily_requests + 1,
                points = points + {ph}
            WHERE user_id = {ph}""",
        (points, user_id)
    )

    cursor.execute(
        f"SELECT points FROM users WHERE user_id = {ph}",
        (user_id,)
    )
    row = cursor.fetchone()
    if row:
        level_info = get_level_info(row[0])
        cursor.execute(
            f"UPDATE users SET level = {ph} WHERE user_id = {ph}",
            (level_info["level"], user_id)
        )

    conn.commit()
    cursor.close()
    conn.close()


def check_limit(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    cursor.execute(
        f"SELECT plan, daily_requests, points FROM users WHERE user_id = {ph}",
        (user_id,)
    )
    row = cursor.fetchone()
    cursor.close()
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

    level_info = get_level_info(points)
    bonus = (level_info["level"] - 1) * 2
    limit += bonus

    if daily_requests >= limit:
        return False, 0

    return True, limit - daily_requests


def get_user_plan(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    cursor.execute(
        f"SELECT plan FROM users WHERE user_id = {ph}",
        (user_id,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row[0] if row else "free"


def set_user_plan(user_id, plan):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    cursor.execute(
        f"UPDATE users SET plan = {ph} WHERE user_id = {ph}",
        (plan, user_id)
    )
    conn.commit()
    cursor.close()
    conn.close()


# ===== الهدية اليومية =====
def claim_daily_gift(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    cursor.execute(
        f"SELECT last_daily_claim, daily_streak FROM users WHERE user_id = {ph}",
        (user_id,)
    )
    row = cursor.fetchone()

    if not row:
        cursor.close()
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
            cursor.close()
            conn.close()
            return {
                "success": False,
                "message": f"⏳ استنى {hours} ساعة و {minutes} دقيقة",
                "remaining_hours": hours,
            }

        if diff > timedelta(hours=48):
            streak = 0
        else:
            streak += 1
    else:
        streak = 1

    points = POINTS_REWARDS["daily_gift"]
    bonus = 0

    if streak == 7:
        bonus = POINTS_REWARDS["streak_bonus_7"]
    elif streak == 30:
        bonus = POINTS_REWARDS["streak_bonus_30"]

    total = points + bonus

    cursor.execute(
        f"UPDATE users SET last_daily_claim = {ph}, daily_streak = {ph}, points = points + {ph} WHERE user_id = {ph}",
        (now.strftime("%Y-%m-%d %H:%M:%S"), streak, total, user_id)
    )

    cursor.execute(
        f"SELECT points FROM users WHERE user_id = {ph}",
        (user_id,)
    )
    new_points = cursor.fetchone()[0]
    level_info = get_level_info(new_points)

    cursor.execute(
        f"UPDATE users SET level = {ph} WHERE user_id = {ph}",
        (level_info["level"], user_id)
    )

    conn.commit()
    cursor.close()
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


# ===== المتصدرين =====
def get_leaderboard(limit=10):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    cursor.execute(
        f"""SELECT user_id, first_name, username, points, level
            FROM users
            ORDER BY points DESC
            LIMIT {ph}""",
        (limit,)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


# ===== الإحصائيات =====
def get_detailed_stats():
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    today = str(date.today())
    cursor.execute(
        f"SELECT COUNT(*) FROM users WHERE last_used = {ph}",
        (today,)
    )
    active_today = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE plan = 'premium'")
    premium_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE plan = 'admin'")
    admin_users = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(total_requests) FROM users")
    total_requests = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(points) FROM users")
    total_points = cursor.fetchone()[0] or 0

    cursor.execute("""
        SELECT first_name, points FROM users
        ORDER BY points DESC LIMIT 5
    """)
    top_users = cursor.fetchall()

    cursor.close()
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


def get_all_users(limit=20):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    cursor.execute(
        f"""SELECT user_id, first_name, username, points, level, plan, last_used
            FROM users
            ORDER BY last_used DESC
            LIMIT {ph}""",
        (limit,)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def get_all_user_ids():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM users WHERE plan != 'banned'")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [row[0] for row in rows]


# ===== دوال المواد =====
def get_user_subjects(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    cursor.execute(
        f"SELECT subject_name FROM user_subjects WHERE user_id = {ph} AND is_active = 1 ORDER BY id",
        (user_id,)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [row[0] for row in rows]


def add_subject(user_id, subject_name):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    cursor.execute(
        f"SELECT id FROM user_subjects WHERE user_id = {ph} AND subject_name = {ph} AND is_active = 1",
        (user_id, subject_name)
    )
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return False

    cursor.execute(
        f"INSERT INTO user_subjects (user_id, subject_name, added_date) VALUES ({ph}, {ph}, {ph})",
        (user_id, subject_name, str(date.today()))
    )
    conn.commit()
    cursor.close()
    conn.close()
    return True


def delete_subject(user_id, subject_name):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    cursor.execute(
        f"UPDATE user_subjects SET is_active = 0 WHERE user_id = {ph} AND subject_name = {ph}",
        (user_id, subject_name)
    )
    conn.commit()
    cursor.close()
    conn.close()


def clear_user_subjects(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    cursor.execute(
        f"UPDATE user_subjects SET is_active = 0 WHERE user_id = {ph}",
        (user_id,)
    )
    conn.commit()
    cursor.close()
    conn.close()


def has_subjects(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    cursor.execute(
        f"SELECT COUNT(*) FROM user_subjects WHERE user_id = {ph} AND is_active = 1",
        (user_id,)
    )
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return count > 0


# ===== دوال التحليل الشخصي =====
def save_analysis(user_id, study_time, focus_duration, learning_style, hard_subject, goal, exam_timing, analysis_result):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        f"DELETE FROM user_analysis WHERE user_id = {ph}",
        (user_id,)
    )

    cursor.execute(
        f"""INSERT INTO user_analysis 
            (user_id, study_time, focus_duration, learning_style, hard_subject, goal, exam_timing, analysis_result, analysis_date)
            VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})""",
        (user_id, study_time, focus_duration, learning_style, hard_subject, goal, exam_timing, analysis_result, now)
    )

    conn.commit()
    cursor.close()
    conn.close()


def get_analysis(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    cursor.execute(
        f"""SELECT study_time, focus_duration, learning_style, hard_subject, 
                   goal, exam_timing, analysis_result, analysis_date
            FROM user_analysis WHERE user_id = {ph}""",
        (user_id,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row:
        return {
            "study_time": row[0],
            "focus_duration": row[1],
            "learning_style": row[2],
            "hard_subject": row[3],
            "goal": row[4],
            "exam_timing": row[5],
            "analysis_result": row[6],
            "analysis_date": row[7],
        }
    return None


def has_analysis(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    cursor.execute(
        f"SELECT COUNT(*) FROM user_analysis WHERE user_id = {ph}",
        (user_id,)
    )
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return count > 0


# ============================================
# ===== دوال خطة المذاكرة (جديد - المرحلة 2) =====
# ============================================

def save_study_plan(user_id, plan_text, plan_json=None):
    """بيحفظ خطة المذاكرة"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        f"DELETE FROM study_plans WHERE user_id = {ph}",
        (user_id,)
    )

    cursor.execute(
        f"""INSERT INTO study_plans 
            (user_id, plan_text, plan_json, created_date, updated_date)
            VALUES ({ph}, {ph}, {ph}, {ph}, {ph})""",
        (user_id, plan_text, plan_json, now, now)
    )

    conn.commit()
    cursor.close()
    conn.close()


def get_study_plan(user_id):
    """بيرجع خطة المذاكرة"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    cursor.execute(
        f"""SELECT plan_text, plan_json, created_date, updated_date
            FROM study_plans WHERE user_id = {ph}""",
        (user_id,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row:
        return {
            "plan_text": row[0],
            "plan_json": row[1],
            "created_date": row[2],
            "updated_date": row[3],
        }
    return None


def has_study_plan(user_id):
    """بيتحقق لو المستخدم عنده خطة"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    cursor.execute(
        f"SELECT COUNT(*) FROM study_plans WHERE user_id = {ph}",
        (user_id,)
    )
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return count > 0


# ===== دوال Pomodoro =====
def save_pomodoro_session(user_id, subject, duration):
    """بيحفظ جلسة Pomodoro"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        f"""INSERT INTO pomodoro_sessions 
            (user_id, subject, duration, session_date)
            VALUES ({ph}, {ph}, {ph}, {ph})""",
        (user_id, subject, duration, now)
    )

    conn.commit()
    cursor.close()
    conn.close()


def get_today_pomodoro_count(user_id):
    """بيرجع عدد جلسات Pomodoro النهاردة"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    today = str(date.today())

    cursor.execute(
        f"""SELECT COUNT(*) FROM pomodoro_sessions 
            WHERE user_id = {ph} AND session_date LIKE {ph}""",
        (user_id, f"{today}%")
    )
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return count


def get_today_pomodoro_minutes(user_id):
    """بيرجع عدد دقائق Pomodoro النهاردة"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    today = str(date.today())

    cursor.execute(
        f"""SELECT COALESCE(SUM(duration), 0) FROM pomodoro_sessions 
            WHERE user_id = {ph} AND session_date LIKE {ph}""",
        (user_id, f"{today}%")
    )
    minutes = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return minutes


def get_pomodoro_stats(user_id, days=7):
    """إحصائيات Pomodoro لآخر N أيام"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    cursor.execute(
        f"""SELECT COUNT(*), COALESCE(SUM(duration), 0) FROM pomodoro_sessions 
            WHERE user_id = {ph} AND session_date >= {ph}""",
        (user_id, start_date)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    return {
        "sessions": row[0] if row else 0,
        "minutes": row[1] if row else 0,
    }