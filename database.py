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
    from psycopg2 import pool
    USE_POSTGRES = True
    print("✅ باستخدام PostgreSQL (مع Connection Pooling)")

    # ===== Connection Pool =====
    try:
        _connection_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=2,
            maxconn=20,
            dsn=DATABASE_URL
        )
        print("✅ Connection Pool جاهز (min=2, max=20)")
    except Exception as e:
        print(f"❌ فشل إنشاء Connection Pool: {e}")
        _connection_pool = None
else:
    USE_POSTGRES = False
    _connection_pool = None
    print("✅ باستخدام SQLite")


# ===== دوال مساعدة =====
def get_connection():
    """بترجع اتصال من الـ Pool (أو SQLite)"""
    if USE_POSTGRES:
        if _connection_pool is None:
            raise Exception("Connection Pool مش متاح")
        return _connection_pool.getconn()
    else:
        return sqlite3.connect(DATABASE_FILE, timeout=30)


def release_connection(conn):
    """بترجع الاتصال للـ Pool"""
    if USE_POSTGRES and _connection_pool is not None:
        try:
            _connection_pool.putconn(conn)
        except Exception as e:
            print(f"⚠️ خطأ في إرجاع الاتصال: {e}")
    else:
        try:
            conn.close()
        except:
            pass


def placeholder():
    return "%s" if USE_POSTGRES else "?"


# ===== نظام النقاط =====
POINTS_REWARDS = {
    "text_analysis": 5,
    "pdf_analysis": 10,
    "quick_summary": 5,
    "full_explanation": 15,
    "quiz_complete": 15,
    "daily_gift": 5,
    "invite_friend": 20,
    "streak_bonus_7": 50,
    "streak_bonus_30": 500,
    "analysis_done": 30,
    "pomodoro_session": 20,
    "pomodoro_4_sessions": 50,
    "quiz_perfect": 30,
    "mistake_reviewed": 10,
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

    # ============================================
    # ===== الجداول الأساسية (V1) =====
    # ============================================

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
    except Exception:
        conn.rollback()

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN onboarding_done INTEGER DEFAULT 0")
        conn.commit()
    except Exception:
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

    # ===== جدول study_plans =====
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

    # ===== جدول pomodoro_sessions =====
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

    # ===== جدول pdf_analyses =====
    if USE_POSTGRES:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pdf_analyses (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                file_name TEXT,
                page_count INTEGER,
                pdf_text TEXT,
                quick_summary TEXT,
                chapters_json TEXT,
                created_date TEXT
            )
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pdf_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                file_name TEXT,
                page_count INTEGER,
                pdf_text TEXT,
                quick_summary TEXT,
                chapters_json TEXT,
                created_date TEXT
            )
        """)

    # ============================================
    # ===== جداول V2 - Analytics (Phase 0.5) =====
    # ============================================

    # ===== جدول activity_events =====
    if USE_POSTGRES:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_events (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                event_type TEXT NOT NULL,
                metadata TEXT,
                timestamp TEXT NOT NULL
            )
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                metadata TEXT,
                timestamp TEXT NOT NULL
            )
        """)

    # ============================================
    # ===== جداول V2 - Quiz Engine (Phase 1) =====
    # ============================================

    # ===== جدول concepts =====
    if USE_POSTGRES:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS concepts (
                id BIGSERIAL PRIMARY KEY,
                source_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                importance REAL DEFAULT 0.5,
                difficulty REAL DEFAULT 0.5,
                created_at TEXT
            )
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS concepts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                importance REAL DEFAULT 0.5,
                difficulty REAL DEFAULT 0.5,
                created_at TEXT
            )
        """)

    # ===== جدول concept_relationships =====
    if USE_POSTGRES:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS concept_relationships (
                id BIGSERIAL PRIMARY KEY,
                source_id TEXT NOT NULL,
                from_concept_id INTEGER NOT NULL,
                to_concept_id INTEGER NOT NULL,
                relationship_type TEXT,
                confidence REAL DEFAULT 0.5
            )
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS concept_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT NOT NULL,
                from_concept_id INTEGER NOT NULL,
                to_concept_id INTEGER NOT NULL,
                relationship_type TEXT,
                confidence REAL DEFAULT 0.5
            )
        """)

    # ===== جدول questions =====
    if USE_POSTGRES:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id BIGSERIAL PRIMARY KEY,
                source_id TEXT NOT NULL,
                concept_id INTEGER,
                subconcept_id TEXT,
                question_text TEXT NOT NULL,
                options TEXT,
                correct_answer TEXT,
                explanation TEXT,
                difficulty TEXT,
                difficulty_score INTEGER,
                bloom_level TEXT,
                question_type TEXT DEFAULT 'mcq',
                misconception_map TEXT,
                created_at TEXT
            )
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT NOT NULL,
                concept_id INTEGER,
                subconcept_id TEXT,
                question_text TEXT NOT NULL,
                options TEXT,
                correct_answer TEXT,
                explanation TEXT,
                difficulty TEXT,
                difficulty_score INTEGER,
                bloom_level TEXT,
                question_type TEXT DEFAULT 'mcq',
                misconception_map TEXT,
                created_at TEXT
            )
        """)

    # ===== جدول quiz_sessions =====
    if USE_POSTGRES:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_sessions (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                source_type TEXT,
                source_id TEXT,
                mode TEXT,
                difficulty TEXT,
                question_count INTEGER,
                current_question INTEGER DEFAULT 0,
                score INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                started_at TEXT,
                completed_at TEXT
            )
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                source_type TEXT,
                source_id TEXT,
                mode TEXT,
                difficulty TEXT,
                question_count INTEGER,
                current_question INTEGER DEFAULT 0,
                score INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                started_at TEXT,
                completed_at TEXT
            )
        """)

    # ===== جدول quiz_attempts =====
    if USE_POSTGRES:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id BIGSERIAL PRIMARY KEY,
                session_id INTEGER,
                user_id BIGINT NOT NULL,
                question_id INTEGER,
                concept_id INTEGER,
                question_text TEXT,
                correct_answer TEXT,
                user_answer TEXT,
                is_correct INTEGER,
                response_time INTEGER,
                attempt_number INTEGER DEFAULT 1,
                misconception_detected TEXT,
                timestamp TEXT NOT NULL
            )
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                user_id INTEGER NOT NULL,
                question_id INTEGER,
                concept_id INTEGER,
                question_text TEXT,
                correct_answer TEXT,
                user_answer TEXT,
                is_correct INTEGER,
                response_time INTEGER,
                attempt_number INTEGER DEFAULT 1,
                misconception_detected TEXT,
                timestamp TEXT NOT NULL
            )
        """)

    # ===== جدول knowledge_states =====
    if USE_POSTGRES:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_states (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                concept_id INTEGER NOT NULL,
                concept_name TEXT,
                mastery REAL DEFAULT 0.0,
                confidence REAL DEFAULT 0.0,
                attempts INTEGER DEFAULT 0,
                correct INTEGER DEFAULT 0,
                streak INTEGER DEFAULT 0,
                last_correct INTEGER DEFAULT 0,
                last_seen TEXT,
                UNIQUE(user_id, concept_id)
            )
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                concept_id INTEGER NOT NULL,
                concept_name TEXT,
                mastery REAL DEFAULT 0.0,
                confidence REAL DEFAULT 0.0,
                attempts INTEGER DEFAULT 0,
                correct INTEGER DEFAULT 0,
                streak INTEGER DEFAULT 0,
                last_correct INTEGER DEFAULT 0,
                last_seen TEXT,
                UNIQUE(user_id, concept_id)
            )
        """)

    # ===== جدول misconceptions =====
    if USE_POSTGRES:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS misconceptions (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                concept_id INTEGER,
                concept_name TEXT,
                misconception TEXT,
                confidence REAL DEFAULT 0.0,
                evidence_count INTEGER DEFAULT 1,
                first_detected TEXT,
                last_detected TEXT,
                resolved_at TEXT
            )
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS misconceptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                concept_id INTEGER,
                concept_name TEXT,
                misconception TEXT,
                confidence REAL DEFAULT 0.0,
                evidence_count INTEGER DEFAULT 1,
                first_detected TEXT,
                last_detected TEXT,
                resolved_at TEXT
            )
        """)

    # ===== جدول mistake_reviews =====
    if USE_POSTGRES:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mistake_reviews (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                attempt_id INTEGER,
                question_id INTEGER,
                concept_id INTEGER,
                concept_name TEXT,
                mistake_type TEXT,
                misconception_id INTEGER,
                review_status TEXT DEFAULT 'pending',
                review_count INTEGER DEFAULT 0,
                next_review_at TEXT,
                last_reviewed_at TEXT,
                successful_reviews INTEGER DEFAULT 0,
                failed_reviews INTEGER DEFAULT 0,
                created_at TEXT,
                resolved_at TEXT
            )
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mistake_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                attempt_id INTEGER,
                question_id INTEGER,
                concept_id INTEGER,
                concept_name TEXT,
                mistake_type TEXT,
                misconception_id INTEGER,
                review_status TEXT DEFAULT 'pending',
                review_count INTEGER DEFAULT 0,
                next_review_at TEXT,
                last_reviewed_at TEXT,
                successful_reviews INTEGER DEFAULT 0,
                failed_reviews INTEGER DEFAULT 0,
                created_at TEXT,
                resolved_at TEXT
            )
        """)

    conn.commit()
    cursor.close()
    release_connection(conn)
    

# ============================================
# ===== دوال المستخدمين =====
# ============================================

def get_or_create_user(user_id, username, first_name, invited_by=None):
    conn = get_connection()
    cursor = conn.cursor()

    today = str(date.today())
    ph = placeholder()

    try:
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
            release_connection(conn)
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

        onboarding = bool(user[15]) if len(user) > 15 else False

        cursor.close()
        release_connection(conn)

        return {
            "user_id": user[0], "plan": user[7], "daily_requests": daily_requests,
            "total_requests": user[5], "points": user[8], "level": user[9],
            "daily_streak": user[10], "is_new": False, "onboarding_done": onboarding
        }
    except Exception as e:
        print(f"❌ خطأ في get_or_create_user: {e}")
        try:
            conn.rollback()
            cursor.close()
        except:
            pass
        release_connection(conn)
        raise


def complete_onboarding(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"UPDATE users SET onboarding_done = 1 WHERE user_id = {ph}",
            (user_id,)
        )
        conn.commit()
    except Exception as e:
        print(f"❌ خطأ في complete_onboarding: {e}")
        conn.rollback()
    finally:
        cursor.close()
        release_connection(conn)


def is_onboarding_done(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"SELECT onboarding_done FROM users WHERE user_id = {ph}",
            (user_id,)
        )
        row = cursor.fetchone()
        return bool(row[0]) if row else False
    except Exception as e:
        print(f"❌ خطأ في is_onboarding_done: {e}")
        return False
    finally:
        cursor.close()
        release_connection(conn)


def set_user_college(user_id, college):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"UPDATE users SET college = {ph} WHERE user_id = {ph}",
            (college, user_id)
        )
        conn.commit()
    except Exception as e:
        print(f"❌ خطأ في set_user_college: {e}")
        conn.rollback()
    finally:
        cursor.close()
        release_connection(conn)


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
        return row[0] if row and row[0] else None
    except Exception as e:
        print(f"⚠️ خطأ في get_user_college: {e}")
        return None
    finally:
        cursor.close()
        release_connection(conn)


# ============================================
# ===== دوال النقاط =====
# ============================================

def add_points(user_id, amount):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
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
    except Exception as e:
        print(f"❌ خطأ في add_points: {e}")
        conn.rollback()
    finally:
        cursor.close()
        release_connection(conn)


def get_user_points(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"SELECT points, level FROM users WHERE user_id = {ph}",
            (user_id,)
        )
        row = cursor.fetchone()
        return (row[0], row[1]) if row else (0, 1)
    except Exception as e:
        print(f"❌ خطأ في get_user_points: {e}")
        return 0, 1
    finally:
        cursor.close()
        release_connection(conn)


def increment_usage(user_id, points=0):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
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
    except Exception as e:
        print(f"❌ خطأ في increment_usage: {e}")
        conn.rollback()
    finally:
        cursor.close()
        release_connection(conn)


def check_limit(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"SELECT plan, daily_requests, points FROM users WHERE user_id = {ph}",
            (user_id,)
        )
        row = cursor.fetchone()

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
    except Exception as e:
        print(f"❌ خطأ في check_limit: {e}")
        return True, 0
    finally:
        cursor.close()
        release_connection(conn)


def get_user_plan(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"SELECT plan FROM users WHERE user_id = {ph}",
            (user_id,)
        )
        row = cursor.fetchone()
        return row[0] if row else "free"
    except Exception as e:
        print(f"❌ خطأ في get_user_plan: {e}")
        return "free"
    finally:
        cursor.close()
        release_connection(conn)


def set_user_plan(user_id, plan):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"UPDATE users SET plan = {ph} WHERE user_id = {ph}",
            (plan, user_id)
        )
        conn.commit()
    except Exception as e:
        print(f"❌ خطأ في set_user_plan: {e}")
        conn.rollback()
    finally:
        cursor.close()
        release_connection(conn)


# ============================================
# ===== الهدية اليومية =====
# ============================================

def claim_daily_gift(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"SELECT last_daily_claim, daily_streak FROM users WHERE user_id = {ph}",
            (user_id,)
        )
        row = cursor.fetchone()

        if not row:
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

        return {
            "success": True,
            "points": points,
            "bonus": bonus,
            "total": total,
            "streak": streak,
            "new_points": new_points,
            "level": level_info,
        }
    except Exception as e:
        print(f"❌ خطأ في claim_daily_gift: {e}")
        conn.rollback()
        return {"success": False, "message": "حصل خطأ، حاول تاني"}
    finally:
        cursor.close()
        release_connection(conn)


# ============================================
# ===== المتصدرين =====
# ============================================

def get_leaderboard(limit=10):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"""SELECT user_id, first_name, username, points, level
                FROM users
                ORDER BY points DESC
                LIMIT {ph}""",
            (limit,)
        )
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ خطأ في get_leaderboard: {e}")
        return []
    finally:
        cursor.close()
        release_connection(conn)


# ============================================
# ===== الإحصائيات =====
# ============================================

def get_detailed_stats():
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
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

        return {
            "total_users": total_users,
            "active_today": active_today,
            "premium_users": premium_users,
            "admin_users": admin_users,
            "total_requests": total_requests,
            "total_points": total_points,
            "top_users": top_users,
        }
    except Exception as e:
        print(f"❌ خطأ في get_detailed_stats: {e}")
        return {
            "total_users": 0, "active_today": 0, "premium_users": 0,
            "admin_users": 0, "total_requests": 0, "total_points": 0,
            "top_users": [],
        }
    finally:
        cursor.close()
        release_connection(conn)


def get_all_users(limit=20):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"""SELECT user_id, first_name, username, points, level, plan, last_used
                FROM users
                ORDER BY last_used DESC
                LIMIT {ph}""",
            (limit,)
        )
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ خطأ في get_all_users: {e}")
        return []
    finally:
        cursor.close()
        release_connection(conn)


def get_all_user_ids():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT user_id FROM users WHERE plan != 'banned'")
        rows = cursor.fetchall()
        return [row[0] for row in rows]
    except Exception as e:
        print(f"❌ خطأ في get_all_user_ids: {e}")
        return []
    finally:
        cursor.close()
        release_connection(conn)
        

# ============================================
# ===== دوال المواد =====
# ============================================

def get_user_subjects(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"SELECT subject_name FROM user_subjects WHERE user_id = {ph} AND is_active = 1 ORDER BY id",
            (user_id,)
        )
        rows = cursor.fetchall()
        return [row[0] for row in rows]
    except Exception as e:
        print(f"❌ خطأ في get_user_subjects: {e}")
        return []
    finally:
        cursor.close()
        release_connection(conn)


def add_subject(user_id, subject_name):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"SELECT id FROM user_subjects WHERE user_id = {ph} AND subject_name = {ph} AND is_active = 1",
            (user_id, subject_name)
        )
        if cursor.fetchone():
            return False

        cursor.execute(
            f"INSERT INTO user_subjects (user_id, subject_name, added_date) VALUES ({ph}, {ph}, {ph})",
            (user_id, subject_name, str(date.today()))
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ خطأ في add_subject: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        release_connection(conn)


def delete_subject(user_id, subject_name):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"UPDATE user_subjects SET is_active = 0 WHERE user_id = {ph} AND subject_name = {ph}",
            (user_id, subject_name)
        )
        conn.commit()
    except Exception as e:
        print(f"❌ خطأ في delete_subject: {e}")
        conn.rollback()
    finally:
        cursor.close()
        release_connection(conn)


def clear_user_subjects(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"UPDATE user_subjects SET is_active = 0 WHERE user_id = {ph}",
            (user_id,)
        )
        conn.commit()
    except Exception as e:
        print(f"❌ خطأ في clear_user_subjects: {e}")
        conn.rollback()
    finally:
        cursor.close()
        release_connection(conn)


def has_subjects(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"SELECT COUNT(*) FROM user_subjects WHERE user_id = {ph} AND is_active = 1",
            (user_id,)
        )
        count = cursor.fetchone()[0]
        return count > 0
    except Exception as e:
        print(f"❌ خطأ في has_subjects: {e}")
        return False
    finally:
        cursor.close()
        release_connection(conn)


# ============================================
# ===== دوال التحليل الشخصي =====
# ============================================

def save_analysis(user_id, study_time, focus_duration, learning_style, hard_subject, goal, exam_timing, analysis_result):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
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
    except Exception as e:
        print(f"❌ خطأ في save_analysis: {e}")
        conn.rollback()
    finally:
        cursor.close()
        release_connection(conn)


def get_analysis(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"""SELECT study_time, focus_duration, learning_style, hard_subject, 
                       goal, exam_timing, analysis_result, analysis_date
                FROM user_analysis WHERE user_id = {ph}""",
            (user_id,)
        )
        row = cursor.fetchone()

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
    except Exception as e:
        print(f"❌ خطأ في get_analysis: {e}")
        return None
    finally:
        cursor.close()
        release_connection(conn)


def has_analysis(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"SELECT COUNT(*) FROM user_analysis WHERE user_id = {ph}",
            (user_id,)
        )
        count = cursor.fetchone()[0]
        return count > 0
    except Exception as e:
        print(f"❌ خطأ في has_analysis: {e}")
        return False
    finally:
        cursor.close()
        release_connection(conn)


# ============================================
# ===== دوال خطة المذاكرة =====
# ============================================

def save_study_plan(user_id, plan_text, plan_json=None):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
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
    except Exception as e:
        print(f"❌ خطأ في save_study_plan: {e}")
        conn.rollback()
    finally:
        cursor.close()
        release_connection(conn)


def get_study_plan(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"""SELECT plan_text, plan_json, created_date, updated_date
                FROM study_plans WHERE user_id = {ph}""",
            (user_id,)
        )
        row = cursor.fetchone()

        if row:
            return {
                "plan_text": row[0],
                "plan_json": row[1],
                "created_date": row[2],
                "updated_date": row[3],
            }
        return None
    except Exception as e:
        print(f"❌ خطأ في get_study_plan: {e}")
        return None
    finally:
        cursor.close()
        release_connection(conn)


def has_study_plan(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"SELECT COUNT(*) FROM study_plans WHERE user_id = {ph}",
            (user_id,)
        )
        count = cursor.fetchone()[0]
        return count > 0
    except Exception as e:
        print(f"❌ خطأ في has_study_plan: {e}")
        return False
    finally:
        cursor.close()
        release_connection(conn)


# ============================================
# ===== دوال Pomodoro =====
# ============================================

def save_pomodoro_session(user_id, subject, duration):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            f"""INSERT INTO pomodoro_sessions 
                (user_id, subject, duration, session_date)
                VALUES ({ph}, {ph}, {ph}, {ph})""",
            (user_id, subject, duration, now)
        )

        conn.commit()
    except Exception as e:
        print(f"❌ خطأ في save_pomodoro_session: {e}")
        conn.rollback()
    finally:
        cursor.close()
        release_connection(conn)


def get_today_pomodoro_count(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        today = str(date.today())

        cursor.execute(
            f"""SELECT COUNT(*) FROM pomodoro_sessions 
                WHERE user_id = {ph} AND session_date LIKE {ph}""",
            (user_id, f"{today}%")
        )
        count = cursor.fetchone()[0]
        return count
    except Exception as e:
        print(f"❌ خطأ في get_today_pomodoro_count: {e}")
        return 0
    finally:
        cursor.close()
        release_connection(conn)


def get_today_pomodoro_minutes(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        today = str(date.today())

        cursor.execute(
            f"""SELECT COALESCE(SUM(duration), 0) FROM pomodoro_sessions 
                WHERE user_id = {ph} AND session_date LIKE {ph}""",
            (user_id, f"{today}%")
        )
        minutes = cursor.fetchone()[0]
        return minutes
    except Exception as e:
        print(f"❌ خطأ في get_today_pomodoro_minutes: {e}")
        return 0
    finally:
        cursor.close()
        release_connection(conn)


def get_pomodoro_stats(user_id, days=7):
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        cursor.execute(
            f"""SELECT COUNT(*), COALESCE(SUM(duration), 0) FROM pomodoro_sessions 
                WHERE user_id = {ph} AND session_date >= {ph}""",
            (user_id, start_date)
        )
        row = cursor.fetchone()

        return {
            "sessions": row[0] if row else 0,
            "minutes": row[1] if row else 0,
        }
    except Exception as e:
        print(f"❌ خطأ في get_pomodoro_stats: {e}")
        return {"sessions": 0, "minutes": 0}
    finally:
        cursor.close()
        release_connection(conn)


# ============================================
# ===== دوال PDF Analysis =====
# ============================================

def save_pdf_analysis(user_id, file_name, page_count, pdf_text, quick_summary, chapters_json):
    """بيحفظ تحليل PDF كامل"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            f"DELETE FROM pdf_analyses WHERE user_id = {ph}",
            (user_id,)
        )

        cursor.execute(
            f"""INSERT INTO pdf_analyses 
                (user_id, file_name, page_count, pdf_text, quick_summary, chapters_json, created_date)
                VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})""",
            (user_id, file_name, page_count, pdf_text, quick_summary, chapters_json, now)
        )

        conn.commit()
    except Exception as e:
        print(f"❌ خطأ في save_pdf_analysis: {e}")
        conn.rollback()
    finally:
        cursor.close()
        release_connection(conn)


def get_pdf_analysis(user_id):
    """بيرجع تحليل PDF الأخير للمستخدم"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"""SELECT file_name, page_count, pdf_text, quick_summary, chapters_json, created_date
                FROM pdf_analyses WHERE user_id = {ph}
                ORDER BY id DESC LIMIT 1""",
            (user_id,)
        )
        row = cursor.fetchone()

        if row:
            return {
                "file_name": row[0],
                "page_count": row[1],
                "pdf_text": row[2],
                "quick_summary": row[3],
                "chapters_json": row[4],
                "created_date": row[5],
            }
        return None
    except Exception as e:
        print(f"❌ خطأ في get_pdf_analysis: {e}")
        return None
    finally:
        cursor.close()
        release_connection(conn)


def has_pdf_analysis(user_id):
    """بيتحقق لو المستخدم عنده تحليل PDF محفوظ"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"SELECT COUNT(*) FROM pdf_analyses WHERE user_id = {ph}",
            (user_id,)
        )
        count = cursor.fetchone()[0]
        return count > 0
    except Exception as e:
        print(f"❌ خطأ في has_pdf_analysis: {e}")
        return False
    finally:
        cursor.close()
        release_connection(conn)


def clear_pdf_analysis(user_id):
    """بيمسح تحليل PDF"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"DELETE FROM pdf_analyses WHERE user_id = {ph}",
            (user_id,)
        )
        conn.commit()
    except Exception as e:
        print(f"❌ خطأ في clear_pdf_analysis: {e}")
        conn.rollback()
    finally:
        cursor.close()
        release_connection(conn)
        

# ============================================
# ===== دوال V2 - Analytics (Phase 0.5) =====
# ============================================

def log_event(user_id, event_type, metadata=None):
    """بتسجل حدث في activity_events"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        import json
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        meta_str = json.dumps(metadata, ensure_ascii=False) if metadata else None

        cursor.execute(
            f"""INSERT INTO activity_events 
                (user_id, event_type, metadata, timestamp)
                VALUES ({ph}, {ph}, {ph}, {ph})""",
            (user_id, event_type, meta_str, now)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ خطأ في log_event: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        release_connection(conn)


def get_user_events(user_id, limit=50):
    """بترجع أحداث المستخدم"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"""SELECT event_type, metadata, timestamp
                FROM activity_events
                WHERE user_id = {ph}
                ORDER BY id DESC
                LIMIT {ph}""",
            (user_id, limit)
        )
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ خطأ في get_user_events: {e}")
        return []
    finally:
        cursor.close()
        release_connection(conn)


def get_events_by_type(event_type, limit=100):
    """بترجع أحداث من نوع معين"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"""SELECT user_id, metadata, timestamp
                FROM activity_events
                WHERE event_type = {ph}
                ORDER BY id DESC
                LIMIT {ph}""",
            (event_type, limit)
        )
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ خطأ في get_events_by_type: {e}")
        return []
    finally:
        cursor.close()
        release_connection(conn)


def count_events_today(event_type=None):
    """بتحسب أحداث اليوم"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        today = str(date.today())

        if event_type:
            cursor.execute(
                f"""SELECT COUNT(*) FROM activity_events
                    WHERE event_type = {ph} AND timestamp LIKE {ph}""",
                (event_type, f"{today}%")
            )
        else:
            cursor.execute(
                f"""SELECT COUNT(*) FROM activity_events
                    WHERE timestamp LIKE {ph}""",
                (f"{today}%",)
            )

        count = cursor.fetchone()[0]
        return count
    except Exception as e:
        print(f"❌ خطأ في count_events_today: {e}")
        return 0
    finally:
        cursor.close()
        release_connection(conn)


# ============================================
# ===== دوال V2 - Concepts (Phase 1A) =====
# ============================================

def save_concept(source_id, name, description=None, importance=0.5, difficulty=0.5):
    """بيحفظ مفهوم جديد"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            f"""INSERT INTO concepts 
                (source_id, name, description, importance, difficulty, created_at)
                VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph})""",
            (source_id, name, description, importance, difficulty, now)
        )
        conn.commit()

        # نرجع الـ id
        cursor.execute(
            f"SELECT id FROM concepts WHERE source_id = {ph} AND name = {ph} ORDER BY id DESC LIMIT 1",
            (source_id, name)
        )
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception as e:
        print(f"❌ خطأ في save_concept: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        release_connection(conn)


def get_concepts_by_source(source_id):
    """بترجع كل مفاهيم ملف معين"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"""SELECT id, name, description, importance, difficulty
                FROM concepts
                WHERE source_id = {ph}
                ORDER BY importance DESC""",
            (source_id,)
        )
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ خطأ في get_concepts_by_source: {e}")
        return []
    finally:
        cursor.close()
        release_connection(conn)


def get_concept_by_id(concept_id):
    """بترجع مفهوم بالـ ID"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"SELECT id, source_id, name, description, importance, difficulty FROM concepts WHERE id = {ph}",
            (concept_id,)
        )
        return cursor.fetchone()
    except Exception as e:
        print(f"❌ خطأ في get_concept_by_id: {e}")
        return None
    finally:
        cursor.close()
        release_connection(conn)


def save_concept_relationship(source_id, from_concept_id, to_concept_id, relationship_type, confidence=0.5):
    """بيحفظ علاقة بين مفهومين"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"""INSERT INTO concept_relationships 
                (source_id, from_concept_id, to_concept_id, relationship_type, confidence)
                VALUES ({ph}, {ph}, {ph}, {ph}, {ph})""",
            (source_id, from_concept_id, to_concept_id, relationship_type, confidence)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ خطأ في save_concept_relationship: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        release_connection(conn)


def get_concept_relationships(source_id):
    """بترجع كل العلاقات لملف معين"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"""SELECT from_concept_id, to_concept_id, relationship_type, confidence
                FROM concept_relationships
                WHERE source_id = {ph}""",
            (source_id,)
        )
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ خطأ في get_concept_relationships: {e}")
        return []
    finally:
        cursor.close()
        release_connection(conn)


# ============================================
# ===== دوال V2 - Questions (Phase 1A) =====
# ============================================

def save_question(source_id, concept_id, question_text, options, correct_answer,
                  explanation=None, difficulty=None, difficulty_score=None,
                  bloom_level=None, misconception_map=None):
    """بيحفظ سؤال في بنك الأسئلة"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        import json
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        options_str = json.dumps(options, ensure_ascii=False) if options else None
        misc_str = json.dumps(misconception_map, ensure_ascii=False) if misconception_map else None

        cursor.execute(
            f"""INSERT INTO questions 
                (source_id, concept_id, question_text, options, correct_answer,
                 explanation, difficulty, difficulty_score, bloom_level, 
                 question_type, misconception_map, created_at)
                VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})""",
            (source_id, concept_id, question_text, options_str, correct_answer,
             explanation, difficulty, difficulty_score, bloom_level,
             "mcq", misc_str, now)
        )
        conn.commit()

        cursor.execute(
            f"SELECT id FROM questions WHERE source_id = {ph} ORDER BY id DESC LIMIT 1",
            (source_id,)
        )
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception as e:
        print(f"❌ خطأ في save_question: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        release_connection(conn)


def get_questions_by_source(source_id, difficulty=None, limit=50):
    """بترجع أسئلة ملف معين"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        if difficulty:
            cursor.execute(
                f"""SELECT id, concept_id, question_text, options, correct_answer,
                           explanation, difficulty, difficulty_score, bloom_level, misconception_map
                    FROM questions
                    WHERE source_id = {ph} AND difficulty = {ph}
                    ORDER BY difficulty_score ASC
                    LIMIT {ph}""",
                (source_id, difficulty, limit)
            )
        else:
            cursor.execute(
                f"""SELECT id, concept_id, question_text, options, correct_answer,
                           explanation, difficulty, difficulty_score, bloom_level, misconception_map
                    FROM questions
                    WHERE source_id = {ph}
                    ORDER BY difficulty_score ASC
                    LIMIT {ph}""",
                (source_id, limit)
            )
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ خطأ في get_questions_by_source: {e}")
        return []
    finally:
        cursor.close()
        release_connection(conn)


def get_question_by_id(question_id):
    """بترجع سؤال بالـ ID"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"""SELECT id, source_id, concept_id, question_text, options, correct_answer,
                       explanation, difficulty, difficulty_score, bloom_level, misconception_map
                FROM questions WHERE id = {ph}""",
            (question_id,)
        )
        return cursor.fetchone()
    except Exception as e:
        print(f"❌ خطأ في get_question_by_id: {e}")
        return None
    finally:
        cursor.close()
        release_connection(conn)


def count_questions_by_source(source_id):
    """بتحسب عدد الأسئلة لملف معين"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"SELECT COUNT(*) FROM questions WHERE source_id = {ph}",
            (source_id,)
        )
        return cursor.fetchone()[0]
    except Exception as e:
        print(f"❌ خطأ في count_questions_by_source: {e}")
        return 0
    finally:
        cursor.close()
        release_connection(conn)


# ============================================
# ===== دوال V2 - Quiz Sessions (Phase 1B) =====
# ============================================

def create_quiz_session(user_id, source_type, source_id, mode, difficulty, question_count):
    """بينشئ جلسة كويز جديدة"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            f"""INSERT INTO quiz_sessions 
                (user_id, source_type, source_id, mode, difficulty, question_count, 
                 current_question, score, status, started_at)
                VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})""",
            (user_id, source_type, source_id, mode, difficulty, question_count,
             0, 0, "active", now)
        )
        conn.commit()

        cursor.execute(
            f"SELECT id FROM quiz_sessions WHERE user_id = {ph} ORDER BY id DESC LIMIT 1",
            (user_id,)
        )
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception as e:
        print(f"❌ خطأ في create_quiz_session: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        release_connection(conn)


def get_quiz_session(session_id):
    """بترجع جلسة كويز بالـ ID"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"""SELECT id, user_id, source_type, source_id, mode, difficulty, 
                       question_count, current_question, score, status, started_at, completed_at
                FROM quiz_sessions WHERE id = {ph}""",
            (session_id,)
        )
        return cursor.fetchone()
    except Exception as e:
        print(f"❌ خطأ في get_quiz_session: {e}")
        return None
    finally:
        cursor.close()
        release_connection(conn)


def update_quiz_session(session_id, current_question=None, score=None, status=None):
    """بتحدث جلسة كويز"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        updates = []
        params = []

        if current_question is not None:
            updates.append(f"current_question = {ph}")
            params.append(current_question)
        if score is not None:
            updates.append(f"score = {ph}")
            params.append(score)
        if status is not None:
            updates.append(f"status = {ph}")
            params.append(status)
            if status == "completed":
                updates.append(f"completed_at = {ph}")
                params.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        if not updates:
            return False

        params.append(session_id)
        query = f"UPDATE quiz_sessions SET {', '.join(updates)} WHERE id = {ph}"

        cursor.execute(query, tuple(params))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ خطأ في update_quiz_session: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        release_connection(conn)


def get_user_quiz_sessions(user_id, limit=10):
    """بترجع جلسات كويز المستخدم"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"""SELECT id, source_id, mode, difficulty, question_count, score, status, started_at, completed_at
                FROM quiz_sessions
                WHERE user_id = {ph}
                ORDER BY id DESC
                LIMIT {ph}""",
            (user_id, limit)
        )
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ خطأ في get_user_quiz_sessions: {e}")
        return []
    finally:
        cursor.close()
        release_connection(conn)


# ============================================
# ===== دوال V2 - Quiz Attempts (Phase 1B) =====
# ============================================

def save_quiz_attempt(session_id, user_id, question_id, concept_id, question_text,
                      correct_answer, user_answer, is_correct, response_time=None,
                      attempt_number=1, misconception_detected=None):
    """بتحفظ إجابة طالب"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            f"""INSERT INTO quiz_attempts 
                (session_id, user_id, question_id, concept_id, question_text, 
                 correct_answer, user_answer, is_correct, response_time, 
                 attempt_number, misconception_detected, timestamp)
                VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})""",
            (session_id, user_id, question_id, concept_id, question_text,
             correct_answer, user_answer, 1 if is_correct else 0, response_time,
             attempt_number, misconception_detected, now)
        )
        conn.commit()

        cursor.execute(
            f"SELECT id FROM quiz_attempts WHERE session_id = {ph} ORDER BY id DESC LIMIT 1",
            (session_id,)
        )
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception as e:
        print(f"❌ خطأ في save_quiz_attempt: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        release_connection(conn)


def get_session_attempts(session_id):
    """بترجع كل إجابات جلسة معينة"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"""SELECT id, question_id, concept_id, question_text, user_answer, 
                       is_correct, response_time, misconception_detected
                FROM quiz_attempts
                WHERE session_id = {ph}
                ORDER BY id ASC""",
            (session_id,)
        )
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ خطأ في get_session_attempts: {e}")
        return []
    finally:
        cursor.close()
        release_connection(conn)


def get_user_quiz_stats(user_id):
    """بترجع إحصائيات الكويز للمستخدم"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"""SELECT 
                    COUNT(*) as total,
                    SUM(is_correct) as correct,
                    SUM(CASE WHEN is_correct = 0 THEN 1 ELSE 0 END) as wrong
                FROM quiz_attempts
                WHERE user_id = {ph}""",
            (user_id,)
        )
        row = cursor.fetchone()

        if row and row[0]:
            total = row[0] or 0
            correct = row[1] or 0
            wrong = row[2] or 0
            accuracy = (correct / total * 100) if total > 0 else 0

            return {
                "total": total,
                "correct": correct,
                "wrong": wrong,
                "accuracy": round(accuracy, 1),
            }

        return {"total": 0, "correct": 0, "wrong": 0, "accuracy": 0}
    except Exception as e:
        print(f"❌ خطأ في get_user_quiz_stats: {e}")
        return {"total": 0, "correct": 0, "wrong": 0, "accuracy": 0}
    finally:
        cursor.close()
        release_connection(conn)


# ============================================
# ===== دوال V2 - Knowledge States (Phase 1C) =====
# ============================================

def update_knowledge_state(user_id, concept_id, concept_name, is_correct):
    """بتحدث حالة المعرفة للطالب في مفهوم"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # جرب تحديث
        cursor.execute(
            f"""UPDATE knowledge_states
                SET attempts = attempts + 1,
                    correct = correct + {ph},
                    streak = CASE WHEN {ph} = 1 THEN streak + 1 ELSE 0 END,
                    last_correct = {ph},
                    last_seen = {ph}
                WHERE user_id = {ph} AND concept_id = {ph}""",
            (1 if is_correct else 0, 1 if is_correct else 0,
             1 if is_correct else 0, now, user_id, concept_id)
        )

        # لو مفيش، ضيف جديد
        if cursor.rowcount == 0:
            cursor.execute(
                f"""INSERT INTO knowledge_states
                    (user_id, concept_id, concept_name, attempts, correct, streak, last_correct, last_seen)
                    VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})""",
                (user_id, concept_id, concept_name, 1,
                 1 if is_correct else 0,
                 1 if is_correct else 0,
                 1 if is_correct else 0,
                 now)
            )

        # احسب mastery و confidence
        cursor.execute(
            f"""SELECT attempts, correct FROM knowledge_states
                WHERE user_id = {ph} AND concept_id = {ph}""",
            (user_id, concept_id)
        )
        row = cursor.fetchone()

        if row:
            attempts = row[0] or 0
            correct = row[1] or 0
            mastery = correct / attempts if attempts > 0 else 0.0
            confidence = min(1.0, attempts / 10.0)

            cursor.execute(
                f"""UPDATE knowledge_states
                    SET mastery = {ph}, confidence = {ph}
                    WHERE user_id = {ph} AND concept_id = {ph}""",
                (mastery, confidence, user_id, concept_id)
            )

        conn.commit()
        return True
    except Exception as e:
        print(f"❌ خطأ في update_knowledge_state: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        release_connection(conn)


def get_user_knowledge(user_id):
    """بترجع حالة المعرفة لكل المواضيع"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"""SELECT concept_id, concept_name, mastery, confidence, attempts, correct, streak, last_seen
                FROM knowledge_states
                WHERE user_id = {ph}
                ORDER BY mastery ASC""",
            (user_id,)
        )
        rows = cursor.fetchall()

        return [
            {
                "concept_id": row[0],
                "concept_name": row[1],
                "mastery": row[2],
                "confidence": row[3],
                "attempts": row[4],
                "correct": row[5],
                "streak": row[6],
                "last_seen": row[7],
            }
            for row in rows
        ]
    except Exception as e:
        print(f"❌ خطأ في get_user_knowledge: {e}")
        return []
    finally:
        cursor.close()
        release_connection(conn)


def get_user_weak_topics(user_id, threshold=0.5, limit=5):
    """بترجع أضعف المواضيع"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"""SELECT concept_id, concept_name, mastery, confidence, attempts
                FROM knowledge_states
                WHERE user_id = {ph} AND mastery < {ph}
                ORDER BY mastery ASC
                LIMIT {ph}""",
            (user_id, threshold, limit)
        )
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ خطأ في get_user_weak_topics: {e}")
        return []
    finally:
        cursor.close()
        release_connection(conn)


# ============================================
# ===== دوال V2 - Misconceptions (Phase 1C) =====
# ============================================

def save_misconception(user_id, concept_id, concept_name, misconception, confidence=0.5):
    """بيحفظ خطأ مفاهيمي"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # شوف لو موجود
        cursor.execute(
            f"""SELECT id, evidence_count FROM misconceptions
                WHERE user_id = {ph} AND concept_id = {ph} AND misconception = {ph}""",
            (user_id, concept_id, misconception)
        )
        row = cursor.fetchone()

        if row:
            # زود evidence
            new_count = (row[1] or 0) + 1
            new_confidence = min(1.0, confidence * (1 + 0.2 * new_count))

            cursor.execute(
                f"""UPDATE misconceptions
                    SET evidence_count = {ph}, confidence = {ph}, last_detected = {ph}
                    WHERE id = {ph}""",
                (new_count, new_confidence, now, row[0])
            )
        else:
            # ضيف جديد
            cursor.execute(
                f"""INSERT INTO misconceptions
                    (user_id, concept_id, concept_name, misconception, confidence,
                     evidence_count, first_detected, last_detected)
                    VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})""",
                (user_id, concept_id, concept_name, misconception,
                 confidence, 1, now, now)
            )

        conn.commit()
        return True
    except Exception as e:
        print(f"❌ خطأ في save_misconception: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        release_connection(conn)


def get_user_misconceptions(user_id, concept_id=None):
    """بترجع الأخطاء المفاهيمية للمستخدم"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        if concept_id:
            cursor.execute(
                f"""SELECT id, concept_id, concept_name, misconception, confidence, evidence_count
                    FROM misconceptions
                    WHERE user_id = {ph} AND concept_id = {ph} AND resolved_at IS NULL
                    ORDER BY confidence DESC""",
                (user_id, concept_id)
            )
        else:
            cursor.execute(
                f"""SELECT id, concept_id, concept_name, misconception, confidence, evidence_count
                    FROM misconceptions
                    WHERE user_id = {ph} AND resolved_at IS NULL
                    ORDER BY confidence DESC""",
                (user_id,)
            )
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ خطأ في get_user_misconceptions: {e}")
        return []
    finally:
        cursor.close()
        release_connection(conn)


def resolve_misconception(misconception_id):
    """بيعلّم الخطأ المفاهيمي إنه اتحل"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            f"UPDATE misconceptions SET resolved_at = {ph} WHERE id = {ph}",
            (now, misconception_id)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ خطأ في resolve_misconception: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        release_connection(conn)


# ============================================
# ===== دوال V2 - Mistake Reviews (Phase 1F) =====
# ============================================

def create_mistake_review(user_id, attempt_id, question_id, concept_id, concept_name,
                           mistake_type=None, misconception_id=None):
    """بينشئ مراجعة لغلطة"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        now = datetime.now()
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        next_review = (now + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            f"""INSERT INTO mistake_reviews
                (user_id, attempt_id, question_id, concept_id, concept_name,
                 mistake_type, misconception_id, review_status, review_count,
                 next_review_at, created_at)
                VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})""",
            (user_id, attempt_id, question_id, concept_id, concept_name,
             mistake_type, misconception_id, "pending", 0, next_review, now_str)
        )
        conn.commit()

        cursor.execute(
            f"SELECT id FROM mistake_reviews WHERE user_id = {ph} ORDER BY id DESC LIMIT 1",
            (user_id,)
        )
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception as e:
        print(f"❌ خطأ في create_mistake_review: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        release_connection(conn)


def get_due_mistake_reviews(user_id):
    """بترجع الأخطاء اللي محتاجة مراجعة"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            f"""SELECT id, question_id, concept_id, concept_name, mistake_type,
                       review_count, next_review_at
                FROM mistake_reviews
                WHERE user_id = {ph} 
                  AND review_status = 'pending'
                  AND next_review_at <= {ph}
                ORDER BY next_review_at ASC""",
            (user_id, now)
        )
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ خطأ في get_due_mistake_reviews: {e}")
        return []
    finally:
        cursor.close()
        release_connection(conn)


def get_all_mistake_reviews(user_id):
    """بترجع كل مراجعات الأخطاء"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        cursor.execute(
            f"""SELECT id, question_id, concept_id, concept_name, mistake_type,
                       review_status, review_count, next_review_at, 
                       successful_reviews, failed_reviews
                FROM mistake_reviews
                WHERE user_id = {ph}
                ORDER BY next_review_at ASC""",
            (user_id,)
        )
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ خطأ في get_all_mistake_reviews: {e}")
        return []
    finally:
        cursor.close()
        release_connection(conn)


def update_mistake_review(review_id, is_correct, new_interval_days):
    """بتحدث مراجعة غلطة بعد إجابة"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        now = datetime.now()
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        next_review = (now + timedelta(days=new_interval_days)).strftime("%Y-%m-%d %H:%M:%S")

        if is_correct:
            cursor.execute(
                f"""UPDATE mistake_reviews
                    SET review_count = review_count + 1,
                        successful_reviews = successful_reviews + 1,
                        last_reviewed_at = {ph},
                        next_review_at = {ph}
                    WHERE id = {ph}""",
                (now_str, next_review, review_id)
            )
        else:
            cursor.execute(
                f"""UPDATE mistake_reviews
                    SET review_count = review_count + 1,
                        failed_reviews = failed_reviews + 1,
                        last_reviewed_at = {ph},
                        next_review_at = {ph}
                    WHERE id = {ph}""",
                (now_str, next_review, review_id)
            )

        conn.commit()
        return True
    except Exception as e:
        print(f"❌ خطأ في update_mistake_review: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        release_connection(conn)


def resolve_mistake_review(review_id):
    """بيعلّم الغلطة إنها اتحلت"""
    conn = get_connection()
    cursor = conn.cursor()
    ph = placeholder()

    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            f"""UPDATE mistake_reviews
                SET review_status = 'mastered', resolved_at = {ph}
                WHERE id = {ph}""",
            (now, review_id)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ خطأ في resolve_mistake_review: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        release_connection(conn)