import os
import json
import re
from groq import Groq
import google.generativeai as genai
from dotenv import load_dotenv
from pypdf import PdfReader
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes
)
from telegram.request import HTTPXRequest

from config import (
    WELCOME_MESSAGE, ABOUT_MESSAGE, BOT_NAME, BOT_VERSION,
    DEVELOPER_NAME, DEVELOPER_USERNAME, ADMIN_IDS, BOT_USERNAME
)
from database import (
    init_db, get_or_create_user, increment_usage,
    check_limit, get_user_plan, set_user_plan, get_detailed_stats,
    add_points, get_user_points, claim_daily_gift,
    get_leaderboard, get_level_info,
    POINTS_REWARDS, LEVELS,
    get_all_users, get_all_user_ids,
    get_user_subjects, add_subject, delete_subject,
    clear_user_subjects, has_subjects,
    set_user_college, get_user_college,
    complete_onboarding, is_onboarding_done,
    save_analysis, get_analysis, has_analysis,
    save_study_plan, get_study_plan, has_study_plan,
    save_pomodoro_session, get_today_pomodoro_count,
    get_today_pomodoro_minutes, get_pomodoro_stats,
    save_pdf_analysis, get_pdf_analysis, has_pdf_analysis,
    clear_pdf_analysis
)
from keyboards import (
    main_menu, pdf_menu, quiz_menu, explain_menu,
    translate_menu, summarize_menu, account_menu,
    back_button, points_menu, analysis_options_menu,
    admin_panel_menu, admin_user_actions,
    skip_subjects_button, subjects_menu,
    analysis_start_menu,
    analysis_q1_time, analysis_q2_duration, analysis_q3_style,
    analysis_q4_hard_subject, analysis_q5_goal, analysis_q6_exams,
    analysis_result_menu, analysis_needed_menu,
    plan_menu, plan_needs_analysis_menu,
    pomodoro_start_menu, pomodoro_duration_menu,
    pomodoro_subjects_menu, pomodoro_active_menu, pomodoro_done_menu,
    quick_actions_menu, chapters_menu, chapter_nav_menu,
    chapter_options_menu, back_to_chapters_menu
)

# ===== الإعدادات =====
load_dotenv()

# Groq (الموديل الأساسي - سريع جداً)
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
GROQ_MODEL = "openai/gpt-oss-120b"
# Gemini (احتياطي)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel("gemini-3.6-flash")

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


# ===== دالة AI موحدة (Groq + Gemini) =====
def ai_generate(prompt, use_groq=True, max_tokens=4000):
    """بتوليد نص بـ Groq أو Gemini"""
    if use_groq:
        try:
            response = groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": "إنت مساعد دراسي مصري. كل ردودك بالعربي."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"⚠️ Groq فشل: {e}")
            print("⏳ بنجرب Gemini...")
            use_groq = False

    if not use_groq:
        try:
            response = gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"⚠️ Gemini فشل كمان: {e}")
            return "❌ حصل خطأ في الاتصال بالـ AI. حاول تاني."


# ===== دالة آمنة لتعديل الرسائل =====
async def safe_edit(query, text, parse_mode=None, reply_markup=None):
    """بتعدل الرسالة بأمان — بدون parse_mode"""
    try:
        if len(text) > 4000:
            await query.edit_message_text(text[:4000])
            await query.message.reply_text(
                text[4000:],
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_text(
                text,
                reply_markup=reply_markup
            )
    except Exception as e:
        error_str = str(e)
        if "Message is not modified" in error_str:
            print(f"ℹ️ Message not modified (تجاهل)")
        else:
            print(f"⚠️ خطأ في edit_message_text: {e}")
            try:
                await query.message.reply_text(
                    text[:4000] if len(text) > 4000 else text,
                    reply_markup=reply_markup
                )
            except Exception as e2:
                print(f"⚠️ خطأ في reply_text: {e2}")


# ===== دالة تنظيف النص =====
def clean_text(text):
    """تنظيف النص من علامات Markdown"""
    if not text:
        return ""

    text = text.replace("###", "▪")
    text = text.replace("##", "◈")
    text = text.replace("#", "•")
    text = text.replace("**", "")
    text = text.replace("---", "━━━━━━━━━━━━━")

    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if line.startswith("*") and not line.startswith("**"):
            line = "• " + line[1:].strip()
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


# ===== دالة تقسيم النص =====
def chunk_pdf_text(pdf_text, chunk_size=15000):
    """بتقسم النص لأجزاء"""
    chunks = []
    for i in range(0, len(pdf_text), chunk_size):
        chunks.append(pdf_text[i:i+chunk_size])
    return chunks


# ===== دوال AI =====
def translate_text(text, target_language="الإنجليزية"):
    prompt = f"إنت مترجم محترف. ترجم النص ده لـ {target_language} فقط، بدون أي إضافات:\n\n{text}"
    return ai_generate(prompt, max_tokens=2000)


def summarize_text(text):
    prompt = f"لخص النص ده في 3 نقاط بس، بالعربي:\n\n{text}"
    return ai_generate(prompt, max_tokens=1000)


def process_pdf(file_path):
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text


def analyze_pdf_content(text, analysis_type="summary", user_subjects=None, user_college=None):
    """تحليل PDF — كله بالعربي"""
    if len(text) > 15000:
        text = text[:15000] + "..."

    context_parts = ["إنت مساعد طالب جامعي."]

    if user_college:
        context_parts.append(f"الطالب في كلية: {user_college}.")

    if user_subjects:
        subjects_str = ", ".join(user_subjects)
        context_parts.append(f"مواد الطالب: {subjects_str}.")

    subjects_context = "\n".join(context_parts)

    base_prompt = f"""{subjects_context}

⚠️ مهم:
- كل الشرح بالعربي فقط
- اكتب المصطلحات الأجنبية (إنجليزي) + العربي
- نظّم النص بعناوين عريضة **نص**
- سيب سطر فاضي بين الأقسام
"""

    prompts = {
        "summary": f"""{base_prompt}

📄 المحتوى:
{text}

━━━━━━━━━━━━━━━

اعملي ملخص سريع بالعربي في 5-7 نقاط أساسية.""",

        "terms": f"""{base_prompt}

📄 المحتوى:
{text}

━━━━━━━━━━━━━━━

اعملي قائمة المصطلحات:

**🔤 المصطلح:**
📖 المعنى بالعربي
💡 مثال""",

        "quiz": f"""{base_prompt}

📄 المحتوى:
{text}

━━━━━━━━━━━━━━━

اعملي 5 أسئلة اختيارات:

**السؤال 1:**
السؤال؟
أ) خيار 1
ب) خيار 2
ج) خيار 3
د) خيار 4
✅ الإجابة: (أ/ب/ج/د)""",

        "examples": f"""{base_prompt}

📄 المحتوى:
{text}

━━━━━━━━━━━━━━━

اعملي 5 أمثلة عملية:

🎯 المفهوم
💡 المثال
📝 الشرح""",
    }

    prompt = prompts.get(analysis_type, prompts["summary"])
    return ai_generate(prompt, max_tokens=3000)


def generate_quick_summary(pdf_text, user_college=None, user_subjects=None):
    """ملخص سريع (10 ثواني)"""
    if len(pdf_text) > 15000:
        pdf_text = pdf_text[:15000] + "..."

    context = ""
    if user_college:
        context += f"الطالب في كلية: {user_college}.\n"
    if user_subjects:
        context += f"مواده: {', '.join(user_subjects)}.\n"

    prompt = f"""إنت مساعد طالب جامعي.

{context}

المحتوى:
{pdf_text}

━━━━━━━━━━━━━━━

🎯 اعمل ملخص سريع جداً بالعربي:

⚠️ القواعد:
- 5-7 نقاط بس
- كل نقطة سطر واحد
- من غير تفاصيل
- اكتب بالعربي

الشكل:

📝 **الملخص السريع:**

• النقطة 1
• النقطة 2
...

📊 **عن الملف:**
- الموضوع: ...
- المستوى: [مبتدئ/متوسط/متقدم]"""

    return ai_generate(prompt, max_tokens=1500)


def generate_chapters(pdf_text, user_college=None, user_subjects=None, learning_style=None):
    """يقسم المحتوى لفصول وأجزاء — مع chunks"""
    context = ""
    if user_college:
        context += f"الطالب في كلية: {user_college}.\n"
    if user_subjects:
        context += f"مواده: {', '.join(user_subjects)}.\n"

    # لو النص صغير
    if len(pdf_text) <= 20000:
        prompt = f"""إنت "ذاكر" — مدرب دراسي مصري.

{context}

المحتوى:
{pdf_text}

━━━━━━━━━━━━━━━

🎯 قسّم المحتوى ده لفصول وأجزاء:

⚠️ المطلوب:
- 3-5 فصول منطقية
- كل فصل فيه 3-5 أجزاء
- كل جزء عنوان واضح
- الترتيب منطقي

⚠️ رد بـ JSON فقط، بدون كلام إضافي:

{{
  "chapters": [
    {{
      "title": "اسم الفصل",
      "parts": [
        {{"title": "عنوان الجزء 1"}},
        {{"title": "عنوان الجزء 2"}}
      ]
    }}
  ]
}}"""

        response = ai_generate(prompt, max_tokens=2000)

        try:
            text = response.strip()
            text = text.replace("```json", "").replace("```", "").strip()

            # ابحث عن JSON في النص
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                text = text[start:end]

            data = json.loads(text)
            return data.get("chapters", [])
        except Exception as e:
            print(f"⚠️ خطأ في قراءة JSON: {e}")

    # لو النص كبير — نقسم
    chunks = chunk_pdf_text(pdf_text, 15000)
    print(f"📊 الملف كبير — بنقسمه لـ {len(chunks)} أجزاء")

    all_chapters = []
    for i, chunk in enumerate(chunks[:5]):  # أول 5 أجزاء بس (75,000 حرف)
        prompt = f"""إنت "ذاكر".

{context}

الجزء {i+1} من الملف:
{chunk}

━━━━━━━━━━━━━━━

🎯 قسّم الجزء ده لـ 2-3 فصول فرعية:

⚠️ رد بـ JSON:

{{
  "chapters": [
    {{
      "title": "الفصل الفرعي",
      "parts": [{{"title": "الجزء"}}]
    }}
  ]
}}"""

        response = ai_generate(prompt, max_tokens=1500)

        try:
            text = response.strip()
            text = text.replace("```json", "").replace("```", "").strip()

            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                text = text[start:end]

            data = json.loads(text)
            sub_chapters = data.get("chapters", [])

            # نضيف رقم الجزء الرئيسي للاسم
            for ch in sub_chapters:
                ch["title"] = f"[جزء {i+1}] {ch.get('title', '')}"
                all_chapters.append(ch)
        except Exception as e:
            print(f"⚠️ خطأ في جزء {i+1}: {e}")
            continue

    # لو مفيش فصول
    if not all_chapters:
        all_chapters = [
            {"title": "الفصل 1", "parts": [{"title": "الجزء 1"}, {"title": "الجزء 2"}]},
            {"title": "الفصل 2", "parts": [{"title": "الجزء 1"}, {"title": "الجزء 2"}]},
            {"title": "الفصل 3", "parts": [{"title": "الجزء 1"}, {"title": "الجزء 2"}]},
        ]

    return all_chapters


def generate_chapter_explanation(pdf_text, chapter_title, parts, user_analysis=None, user_college=None, user_subjects=None):
    """يشرح فصل كامل — كل حاجة بالعربي"""
    if len(pdf_text) > 15000:
        pdf_text = pdf_text[:15000] + "..."

    analysis_context = ""
    if user_analysis:
        learning_style = user_analysis.get("learning_style", "")
        goal = user_analysis.get("goal", "")
        if learning_style:
            analysis_context += f"نمط تعلمه: {learning_style}.\n"
        if goal:
            analysis_context += f"هدفه: {goal}.\n"

    if user_college:
        analysis_context += f"كلية: {user_college}.\n"
    if user_subjects:
        analysis_context += f"مواده: {', '.join(user_subjects)}.\n"

    parts_text = "\n".join([f"- {p.get('title', 'جزء')}" for p in parts])

    prompt = f"""إنت "ذاكر" — مدرب دراسي مصري.

معلومات الطالب:
{analysis_context}

📚 الفصل: {chapter_title}
الأجزاء: {parts_text}

📄 المحتوى:
{pdf_text}

━━━━━━━━━━━━━━━

🎯 اشرح الفصل ده بالعربي:

⚠️ القواعد:
1. كل حاجة بالعربي
2. المصطلحات (English) + العربي
3. التنظيم:
   - **📌 [القسم]**
   - • نقطة
   - • مثال
4. سطر فاضي بين الأقسام
5. طول مناسب (1500-2500 كلمة)

الشكل:

📚 **{chapter_title}**

━━━━━━━━━━━━━━━

**📌 [القسم الأول]**

شرح...
• نقطة

   • مثال: ...
   → شرح المثال


**📌 [القسم التاني]**

...


━━━━━━━━━━━━━━━

**💡 ملخص سريع:**
1. ...
2. ..."""

    return ai_generate(prompt, max_tokens=4000)


def generate_study_plan(analysis, subjects, college):
    subjects_str = ", ".join(subjects) if subjects else "مش محدد"

    study_time_map = {
        "morning": "الصبح (6-12)",
        "afternoon": "العصر (12-5)",
        "evening": "بالليل (5-10)",
        "night": "بعد منتصف الليل",
    }

    focus_map = {
        "15": "15 دقيقة",
        "25": "25 دقيقة",
        "45": "45 دقيقة",
        "60": "ساعة",
    }

    style_map = {
        "visual": "بصري",
        "video": "بالفيديو",
        "reading": "بالقراءة",
        "practice": "بالممارسة",
    }

    exam_map = {
        "week": "بعد أسبوع",
        "month": "بعد شهر",
        "2months": "بعد شهرين",
        "unknown": "مش محدد",
    }

    study_time = study_time_map.get(analysis.get("study_time"), "غير محدد")
    focus = focus_map.get(analysis.get("focus_duration"), "غير محدد")
    style = style_map.get(analysis.get("learning_style"), "غير محدد")
    exam = exam_map.get(analysis.get("exam_timing"), "غير محدد")
    hard_subject = analysis.get("hard_subject", "غير محدد")

    prompt = f"""إنت "ذاكر" - مدرب دراسي مصري.

معلومات الطالب:
- الكلية: {college or "غير محددة"}
- المواد: {subjects_str}
- وقت المذاكرة: {study_time}
- مدة التركيز: {focus}
- نمط التعلم: {style}
- أصعب مادة: {hard_subject}
- الامتحانات: {exam}

اعمله خطة أسبوعية بالعربي:

📅 **السبت:**
📚 [المادة] - [المدة]
⏰ [الوقت]

📅 **الأحد:**
...

━━━━━━━━━━━━━━━

💡 **نصائح مخصصة:**
• نصيحة 1
• نصيحة 2
• نصيحة 3

━━━━━━━━━━━━━━━

📊 **إجمالي:**
⏱️ [X] ساعة/أسبوع
📚 [Y] مادة"""

    return ai_generate(prompt, max_tokens=2500)


# ===== دوال مساعدة =====
def format_level_bar(points, level_info):
    min_pts = level_info["min_points"]
    max_pts = level_info["max_points"]

    if max_pts == 999999:
        return "🎉 أقصى مستوى!"

    progress = points - min_pts
    total = max_pts - min_pts
    percent = int((progress / total) * 100) if total > 0 else 0

    filled = int(percent / 10)
    bar = "█" * filled + "░" * (10 - filled)

    return f"{bar} {percent}%"


def get_subject_display(subject_code):
    mapping = {
        "morning": "🌅 الصبح (6-12)",
        "afternoon": "☀️ العصر (12-5)",
        "evening": "🌙 بالليل (5-10)",
        "night": "🦉 بعد منتصف الليل",
        "15": "⏰ 15 دقيقة",
        "25": "⏰ 25 دقيقة",
        "45": "⏰ 45 دقيقة",
        "60": "⏰ ساعة أو أكتر",
        "visual": "📊 بالرسومات",
        "video": "🎬 بالفيديو",
        "reading": "📖 بالقراءة",
        "practice": "💪 بالممارسة",
        "pass": "📝 أنجح بس",
        "excel": "🏆 أتفوق",
        "work": "💼 أشتغل",
        "study": "🎓 أكمل دراسات",
        "week": "🔥 بعد أسبوع",
        "month": "📅 بعد شهر",
        "2months": "🗓️ بعد شهرين أو أكتر",
        "unknown": "⏳ مش عارف",
        "skip": "لم يجب",
    }
    return mapping.get(subject_code, subject_code)


# ===== دالة الترحيب =====
async def send_welcome(update_or_message, user, is_edit=False):
    plan = get_user_plan(user.id)
    allowed, remaining = check_limit(user.id)
    points, level = get_user_points(user.id)
    level_info = get_level_info(points)
    subjects = get_user_subjects(user.id)
    college = get_user_college(user.id)

    plan_names = {
        "free": "🆓 مجاني",
        "premium": "⭐ مميز",
        "admin": "👑 أدمن",
    }

    subjects_text = "، ".join(subjects[:3]) if subjects else "مفيش"
    if len(subjects) > 3:
        subjects_text += f" + {len(subjects)-3}"

    welcome = (
        f"أهلاً {user.first_name}! 👋\n\n"
        f"🎓 *ذاكر* - مساعدك الدراسي\n\n"
        f"💎 *نقاطك:* {points}\n"
        f"🏆 *مستواك:* {level_info['name']}\n"
        f"👤 *حسابك:* {plan_names.get(plan, 'مجاني')}\n"
        f"📊 *متبقي اليوم:* {remaining} استخدام\n"
        f"🎓 *كليتك:* {college or 'لسه'}\n"
        f"📚 *موادك:* {subjects_text}\n\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"*اختار من الأزرار تحت* 👇"
    )

    is_admin = user.id in ADMIN_IDS

    if is_edit:
        try:
            await update_or_message.edit_text(welcome, reply_markup=main_menu(is_admin=is_admin))
        except Exception as e:
            print(f"⚠️ {e}")
    else:
        await update_or_message.reply_text(
            welcome,
            reply_markup=main_menu(is_admin=is_admin)
        )


# ===== الأوامر =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    invited_by = None
    if context.args and len(context.args) > 0:
        arg = context.args[0]
        if arg.startswith("invite_"):
            try:
                invited_by = int(arg.replace("invite_", ""))
            except:
                pass

    get_or_create_user(user.id, user.username, user.first_name, invited_by)

    if not has_subjects(user.id):
        await update.message.reply_text(
            f"أهلاً {user.first_name}! 👋\n\n"
            f"🎓 إنت في *ذاكر* - مساعدك الدراسي\n\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"قبل ما نبدأ:\n\n"
            f"📚 *اكتب المواد اللي بتدرسها*\n"
            f"(كل مادة في سطر)\n\n"
            f"مثال:\n"
            f"Algorithms\n"
            f"Database\n"
            f"Machine Learning\n\n"
            f"أو اختار من الأزرار تحت 👇",
            reply_markup=skip_subjects_button()
        )
        return

    user_college = get_user_college(user.id)
    if not user_college:
        context.user_data["awaiting_college"] = True
        await update.message.reply_text(
            f"📚 تمام! موادي محفوظة ✅\n\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"🎓 عايز أعرف *إنت في أي كلية*:\n\n"
            f"اكتب اسم كليتك:"
        )
        return

    complete_onboarding(user.id)
    await send_welcome(update.message, user)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📚 *الأوامر المتاحة:*\n\n"
        "/start - البداية\n"
        "/help - مساعدة\n"
        "/about - عن ذاكر\n"
        "/myplan - خطتك\n"
        "/points - نقاطك\n"
        "/daily - هدية يومية\n"
        "/leaderboard - المتصدرين\n"
        "/invite - دعوة أصدقاء\n"
        "/subjects - موادي\n"
        "/analysis - تحليلي"
    )
    await update.message.reply_text(text)


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(ABOUT_MESSAGE)


async def myplan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    plan = get_user_plan(user.id)
    allowed, remaining = check_limit(user.id)

    plan_names = {
        "free": "🆓 مجاني",
        "premium": "⭐ مميز",
        "admin": "👑 أدمن",
    }

    text = (
        f"👤 *حسابك:* {plan_names.get(plan, 'مجاني')}\n"
        f"📊 *متبقي اليوم:* {remaining} استخدام\n\n"
    )

    if plan == "free":
        text += f"💎 *للترقية:* تواصل مع {DEVELOPER_USERNAME}"

    await update.message.reply_text(text)


async def points_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_or_create_user(user.id, user.username, user.first_name)

    points, level = get_user_points(user.id)
    level_info = get_level_info(points)
    bar = format_level_bar(points, level_info)

    text = (
        f"💎 *نقاطك:* {points}\n"
        f"🏆 *مستواك:* {level_info['name']}\n\n"
        f"📊 *التقدم للمستوى الجاي:*\n"
        f"{bar}\n\n"
        f"🎯 عايز نقاط أكتر؟\n"
        f"• استخدم البوت\n"
        f"• استلم هديتك اليومية\n"
        f"• ادعي أصحابك"
    )

    await update.message.reply_text(text, reply_markup=points_menu())


async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_or_create_user(user.id, user.username, user.first_name)

    result = claim_daily_gift(user.id)

    if not result["success"]:
        await update.message.reply_text(f"⚠️ {result['message']}\n\n🔔 متنساش ترجع تاني!")
        return

    text = f"🎉 *مبروك!*\n\n💎 كسبت: *{result['points']}* نقطة\n"

    if result["bonus"] > 0:
        text += f"🎁 بونص السلسلة: *+{result['bonus']}* نقطة\n"

    text += (
        f"\n🔥 *سلسلتك:* {result['streak']} يوم\n"
        f"📊 *إجمالي نقاطك:* {result['new_points']}\n"
        f"🏆 *مستواك:* {result['level']['name']}"
    )

    await update.message.reply_text(text)


async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top = get_leaderboard(10)

    if not top:
        await update.message.reply_text("📊 لسه مفيش متصدرين!")
        return

    text = "🏆 *أعلى 10 طلاب:*\n\n"
    medals = ["🥇", "🥈", "🥉"]

    for i, (user_id, first_name, username, points, level) in enumerate(top):
        emoji = medals[i] if i < 3 else f"{i+1}."
        level_info = get_level_info(points)
        name = first_name or "طالب"
        text += f"{emoji} *{name}* — {points} 💎\n"
        text += f"   {level_info['name']}\n\n"

    await update.message.reply_text(text)


async def invite_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_or_create_user(user.id, user.username, user.first_name)

    bot_username = BOT_USERNAME.replace("@", "")
    invite_link = f"https://t.me/{bot_username}?start=invite_{user.id}"

    text = (
        f"👥 *دعوة الأصدقاء*\n\n"
        f"كل صاحب يدخل من لينكك = *20 نقطة* 💎\n\n"
        f"🔗 *لينكك:*\n"
        f"{invite_link}\n\n"
        f"📤 انسخ اللينك وابعته!"
    )

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("📤 مشاركة", url=f"https://t.me/share/url?url={invite_link}")
        ]])
    )


async def subjects_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_or_create_user(user.id, user.username, user.first_name)

    subjects = get_user_subjects(user.id)

    if not subjects:
        text = "📚 *موادي*\n\nلسه مسجلتش مواد.\n\nاختار:"
    else:
        subjects_list = "\n".join([f"{i+1}. {s}" for i, s in enumerate(subjects)])
        text = f"📚 *موادي ({len(subjects)}):*\n\n{subjects_list}\n\nعايز تعدل؟"

    await update.message.reply_text(text, reply_markup=subjects_menu())


async def analysis_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_or_create_user(user.id, user.username, user.first_name)

    if not has_analysis(user.id):
        await update.message.reply_text(
            "🧠 *لسه معملتش التحليل*\n\nالتحليل بياخد 30 ثانية بس!",
            reply_markup=analysis_needed_menu()
        )
        return

    analysis = get_analysis(user.id)

    text = (
        f"🧠 *تحليلك الشخصي*\n\n"
        f"🌙 *وقت مذاكرتك:* {get_subject_display(analysis['study_time'])}\n"
        f"⏱️ *مدة تركيزك:* {get_subject_display(analysis['focus_duration'])}\n"
        f"🧠 *نمط تعلمك:* {get_subject_display(analysis['learning_style'])}\n"
        f"📚 *أصعب مادة:* {analysis['hard_subject']}\n"
        f"🎯 *هدفك:* {get_subject_display(analysis['goal'])}\n"
        f"📅 *امتحاناتك:* {get_subject_display(analysis['exam_timing'])}\n\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"📅 *آخر تحديث:* {analysis['analysis_date']}"
    )

    await update.message.reply_text(text, reply_markup=analysis_result_menu())


# ===== معالجة أزرار التحليل =====
async def handle_analysis_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user = query.from_user

    if data == "analysis_begin" or data == "analysis_restart":
        await query.answer()

        context.user_data["in_analysis"] = True
        context.user_data["analysis_step"] = 1
        context.user_data["analysis_answers"] = {}

        await safe_edit(
            query,
            "📊 *سؤال 1 من 6*\n\n⏰ *إنت بتذاكر إمتى؟*\n\n━━━━━━━━━━━━━━━",
            reply_markup=analysis_q1_time()
        )
        return

    if data == "analysis_cancel":
        await query.answer()
        context.user_data["in_analysis"] = False
        await safe_edit(query, "❌ *تم إلغاء التحليل*")
        return

    if data == "ans_skip":
        await query.answer()
        step = context.user_data.get("analysis_step", 1)
        answers = context.user_data.get("analysis_answers", {})
        answers[f"q{step}"] = "skip"
        context.user_data["analysis_answers"] = answers
        context.user_data["analysis_step"] = step + 1
        await show_next_question(query, context, step + 1)
        return

    if data.startswith("ans_q"):
        await query.answer()
        parts = data.replace("ans_q", "").split("_", 1)
        step = int(parts[0])
        answer = parts[1] if len(parts) > 1 else ""

        answers = context.user_data.get("analysis_answers", {})
        answers[f"q{step}"] = answer
        context.user_data["analysis_answers"] = answers
        context.user_data["analysis_step"] = step + 1

        await show_next_question(query, context, step + 1)
        return


# ===== معالجة أزرار PDF =====
async def handle_pdf_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user = query.from_user

    # Quick Actions
    if data == "quick_summary":
        await query.answer()
        await handle_quick_summary(query, context, user)
        return

    if data == "full_explanation":
        await query.answer()
        await handle_full_explanation(query, context, user)
        return

    if data == "quick_terms":
        await query.answer()
        await handle_pdf_analysis(query, context, user, "terms")
        return

    if data == "quick_quiz":
        await query.answer()
        await handle_pdf_analysis(query, context, user, "quiz")
        return

    if data == "ask_pdf":
        await query.answer()
        await safe_edit(query, "💬 *اسألني عن الملف*\n\nاكتب أي سؤال:")
        context.user_data["awaiting_pdf_question"] = True
        return

    if data == "download_analysis":
        await query.answer("📥 قريب إن شاء الله 🚧")
        return

    # Chapters
    if data == "show_chapters":
        await query.answer()
        await show_chapters_list(query, context, user)
        return

    if data.startswith("chapter_"):
        await query.answer()
        chapter_idx = int(data.replace("chapter_", ""))
        context.user_data["current_chapter"] = chapter_idx
        await show_chapter_parts(query, context, user, chapter_idx)
        return

    if data == "explain_full_chapter":
        await query.answer()
        await handle_explain_chapter(query, context, user)
        return

    if data == "explain_part_by_part":
        await query.answer()
        await safe_edit(query, "📌 *شرح جزء جزء*\n\nاستخدم الأزرار ⬅️➡️ للتنقل.")
        return

    if data == "quiz_this_chapter":
        await query.answer("🎯 قريب إن شاء الله 🚧")
        return

    if data == "download_full_explanation":
        await query.answer("📥 قريب إن شاء الله 🚧")
        return

    # أزرار pdf_ القديمة
    if data.startswith("pdf_"):
        await query.answer()
        analysis_type = data.replace("pdf_", "")
        await handle_pdf_analysis(query, context, user, analysis_type)
        return

    # لو مش بتاع PDF
    await button_handler(update, context)


async def handle_quick_summary(query, context, user):
    """ملخص سريع"""
    await safe_edit(query, "⚡ *جاري إعداد الملخص السريع...*\n\n_10-15 ثانية..._")

    pdf_text = context.user_data.get("pdf_text", "")
    if not pdf_text:
        analysis = get_pdf_analysis(user.id)
        if analysis:
            pdf_text = analysis["pdf_text"]
            quick_summary = analysis["quick_summary"]
            if quick_summary:
                await safe_edit(query, clean_text(quick_summary), reply_markup=quick_actions_menu())
                return

    if not pdf_text:
        await safe_edit(query, "⚠️ الملف مش موجود. ارفعه تاني.")
        return

    user_college = get_user_college(user.id)
    user_subjects = get_user_subjects(user.id)

    try:
        summary = generate_quick_summary(pdf_text, user_college, user_subjects)
        summary = clean_text(summary)
        context.user_data["quick_summary"] = summary

        await safe_edit(query, summary, reply_markup=quick_actions_menu())
        increment_usage(user.id, POINTS_REWARDS["quick_summary"])

    except Exception as e:
        await safe_edit(query, f"❌ حصل خطأ: {str(e)}")


async def handle_full_explanation(query, context, user):
    """شرح تفصيلي (فصول)"""
    await safe_edit(
        query,
        "📚 *جاري تحضير الشرح التفصيلي...*\n\n"
        "_استنى 20-40 ثانية..._"
    )

    pdf_text = context.user_data.get("pdf_text", "")
    if not pdf_text:
        analysis = get_pdf_analysis(user.id)
        if analysis:
            pdf_text = analysis["pdf_text"]

    if not pdf_text:
        await safe_edit(query, "⚠️ الملف مش موجود. ارفعه تاني.")
        return

    user_college = get_user_college(user.id)
    user_subjects = get_user_subjects(user.id)
    user_analysis = get_analysis(user.id)
    learning_style = user_analysis.get("learning_style") if user_analysis else None

    try:
        chapters = generate_chapters(pdf_text, user_college, user_subjects, learning_style)

        if not chapters:
            await safe_edit(query, "❌ مقدرناش نقسم المحتوى.")
            return

        context.user_data["chapters"] = chapters

        save_pdf_analysis(
            user.id,
            context.user_data.get("pdf_file_name", "محاضرة"),
            context.user_data.get("pdf_page_count", 0),
            pdf_text[:30000],
            context.user_data.get("quick_summary", ""),
            json.dumps(chapters, ensure_ascii=False)
        )

        text = (
            f"📚 *الشرح التفصيلي*\n\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"الملف مقسم لـ *{len(chapters)} فصول*:\n\n"
        )

        for i, ch in enumerate(chapters):
            title = ch.get("title", f"الفصل {i+1}")
            parts_count = len(ch.get("parts", []))
            text += f"📖 *{title}* ({parts_count} أجزاء)\n"

        text += "\n━━━━━━━━━━━━━━━\n\nاختار الفصل:"

        await safe_edit(query, text, reply_markup=chapters_menu(chapters))

    except Exception as e:
        await safe_edit(query, f"❌ حصل خطأ: {str(e)}")


async def show_chapters_list(query, context, user):
    chapters = context.user_data.get("chapters", [])

    if not chapters:
        analysis = get_pdf_analysis(user.id)
        if analysis and analysis.get("chapters_json"):
            try:
                chapters = json.loads(analysis["chapters_json"])
                context.user_data["chapters"] = chapters
            except:
                pass

    if not chapters:
        await safe_edit(query, "⚠️ لسه معملتش شرح تفصيلي.")
        return

    text = f"📋 *فهرس الفصول*\n\n━━━━━━━━━━━━━━━\n\n"

    for i, ch in enumerate(chapters):
        title = ch.get("title", f"الفصل {i+1}")
        parts_count = len(ch.get("parts", []))
        text += f"📖 *{title}* ({parts_count} أجزاء)\n"

    await safe_edit(query, text, reply_markup=chapters_menu(chapters))


async def show_chapter_parts(query, context, user, chapter_idx):
    chapters = context.user_data.get("chapters", [])

    if not chapters or chapter_idx >= len(chapters):
        await safe_edit(query, "⚠️ الفصل مش موجود.")
        return

    chapter = chapters[chapter_idx]
    title = chapter.get("title", f"الفصل {chapter_idx+1}")
    parts = chapter.get("parts", [])

    text = f"📖 *{title}*\n\n━━━━━━━━━━━━━━━\n\n"

    for i, part in enumerate(parts):
        part_title = part.get("title", f"الجزء {i+1}")
        text += f"📌 *{part_title}*\n"

    text += "\n━━━━━━━━━━━━━━━\n\n🎯 *إيه اللي عايزه؟*"

    await safe_edit(query, text, reply_markup=chapter_options_menu())


async def handle_explain_chapter(query, context, user):
    chapter_idx = context.user_data.get("current_chapter", 0)
    chapters = context.user_data.get("chapters", [])

    if not chapters or chapter_idx >= len(chapters):
        await safe_edit(query, "⚠️ الفصل مش موجود.")
        return

    chapter = chapters[chapter_idx]
    title = chapter.get("title", f"الفصل {chapter_idx+1}")
    parts = chapter.get("parts", [])

    await safe_edit(query, f"💡 *جاري شرح {title}...*\n\n_15-30 ثانية..._")

    pdf_text = context.user_data.get("pdf_text", "")
    if not pdf_text:
        analysis = get_pdf_analysis(user.id)
        if analysis:
            pdf_text = analysis["pdf_text"]

    if not pdf_text:
        await safe_edit(query, "⚠️ الملف مش موجود.")
        return

    user_college = get_user_college(user.id)
    user_subjects = get_user_subjects(user.id)
    user_analysis = get_analysis(user.id)

    try:
        explanation = generate_chapter_explanation(
            pdf_text, title, parts, user_analysis, user_college, user_subjects
        )
        explanation = clean_text(explanation)

        full_text = (
            f"📖 *{title}*\n\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"{explanation}\n\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"📍 *الفصل {chapter_idx+1} / {len(chapters)}*"
        )

        await safe_edit(query, full_text, reply_markup=back_to_chapters_menu())
        increment_usage(user.id, POINTS_REWARDS["full_explanation"])

    except Exception as e:
        await safe_edit(query, f"❌ حصل خطأ: {str(e)}")


async def handle_pdf_analysis(query, context, user, analysis_type):
    pdf_text = context.user_data.get("pdf_text")
    if not pdf_text:
        await safe_edit(query, "⚠️ الملف مش موجود. ارفعه تاني.")
        return

    types = {
        "summary": "📝 الملخص",
        "terms": "🔤 المصطلحات",
        "quiz": "🎯 الكويز",
        "examples": "💡 الأمثلة",
    }
    type_name = types.get(analysis_type, "📝 التحليل")

    await safe_edit(query, f"⏳ جاري إعداد {type_name}...")

    try:
        user_subjects = get_user_subjects(user.id)
        user_college = get_user_college(user.id)

        result = analyze_pdf_content(pdf_text, analysis_type, user_subjects, user_college)
        result = clean_text(result)

        if len(result) <= 4000:
            await safe_edit(query, result, reply_markup=quick_actions_menu())
        else:
            await safe_edit(query, result[:4000])
            await query.message.reply_text(result[4000:], reply_markup=quick_actions_menu())

        increment_usage(user.id, POINTS_REWARDS["pdf_analysis"])

    except Exception as e:
        await safe_edit(query, f"❌ حصل خطأ: {str(e)}")


# ===== معالجة أزرار Pomodoro =====
async def handle_pomodoro_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user = query.from_user

    if data == "start_pomodoro":
        await query.answer()
        if not has_subjects(user.id):
            await safe_edit(query, "⚠️ ضيف موادك الأول!", reply_markup=subjects_menu())
            return
        await safe_edit(query, "⏱️ *Pomodoro*\n\nاختار:", reply_markup=pomodoro_start_menu())
        return

    if data == "pomodoro_begin" or data == "pomodoro_choose_subject":
        await query.answer()
        subjects = get_user_subjects(user.id)
        await safe_edit(query, "📚 *اختار المادة:*", reply_markup=pomodoro_subjects_menu(subjects))
        return

    if data.startswith("pomodoro_subj_"):
        await query.answer()
        subject = data.replace("pomodoro_subj_", "")
        context.user_data["pomodoro_subject"] = subject
        await safe_edit(
            query,
            f"📚 المادة: {subject}\n\n⏱️ اختار مدة:",
            reply_markup=pomodoro_duration_menu()
        )
        return

    if data in ["pomodoro_15", "pomodoro_25", "pomodoro_45", "pomodoro_60"]:
        await query.answer()
        duration = int(data.replace("pomodoro_", ""))
        subject = context.user_data.get("pomodoro_subject", "مذاكرة")
        await safe_edit(
            query,
            f"⏱️ *جلسة Pomodoro*\n\n📚 {subject}\n⏰ {duration} دقيقة\n\n🚀 يلا!",
            reply_markup=pomodoro_active_menu()
        )
        context.user_data["pomodoro_duration"] = duration
        return

    if data == "pomodoro_done":
        await query.answer()
        subject = context.user_data.get("pomodoro_subject", "مذاكرة")
        duration = context.user_data.get("pomodoro_duration", 25)

        save_pomodoro_session(user.id, subject, duration)
        points_earned = POINTS_REWARDS["pomodoro_session"]

        today_count = get_today_pomodoro_count(user.id)
        bonus_points = POINTS_REWARDS["pomodoro_4_sessions"] if today_count >= 4 else 0

        add_points(user.id, points_earned + bonus_points)

        text = (
            f"🎉 *عاش!*\n\n"
            f"📚 {subject}\n"
            f"⏰ {duration} دقيقة\n"
            f"💎 كسبت: *{points_earned} نقطة*\n"
        )

        if bonus_points > 0:
            text += f"🎁 بونص: +{bonus_points}\n"

        text += f"\n🔥 *جلسات النهاردة:* {today_count}"

        await safe_edit(query, text, reply_markup=pomodoro_done_menu())
        return

    if data == "pomodoro_pause":
        await query.answer("⏸️ الجلسة شغالة!")
        return

    if data == "pomodoro_cancel":
        await query.answer()
        await safe_edit(query, "❌ تم إلغاء الجلسة")
        return

    if data == "pomodoro_again":
        await query.answer()
        subjects = get_user_subjects(user.id)
        await safe_edit(query, "📚 اختار المادة:", reply_markup=pomodoro_subjects_menu(subjects))
        return

    if data == "pomodoro_break":
        await query.answer()
        await safe_edit(
            query,
            "☕ *راحة 5 دقايق*\n\n• اشرب حاجة\n• اتمشى",
            reply_markup=pomodoro_done_menu()
        )
        return


# ===== معالجة أزرار الخطة =====
async def handle_plan_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user = query.from_user

    if data == "show_weekly_plan":
        await query.answer()

        if not has_analysis(user.id):
            await safe_edit(query, "⚠️ محتاج تحليل الأول!", reply_markup=plan_needs_analysis_menu())
            return

        if not has_study_plan(user.id):
            await safe_edit(query, "⏳ *جاري إعداد خطتك...*\n\n_20-30 ثانية..._")

            analysis = get_analysis(user.id)
            subjects = get_user_subjects(user.id)
            college = get_user_college(user.id)

            try:
                plan_text = generate_study_plan(analysis, subjects, college)
                plan_text = clean_text(plan_text)
                save_study_plan(user.id, plan_text)
            except Exception as e:
                plan_text = f"❌ حصل خطأ: {str(e)}"

            if len(plan_text) <= 4000:
                await safe_edit(query, plan_text, reply_markup=plan_menu())
            else:
                await safe_edit(query, plan_text[:4000])
                await query.message.reply_text(plan_text[4000:], reply_markup=plan_menu())
            return

        plan = get_study_plan(user.id)
        plan_text = clean_text(plan["plan_text"])

        if len(plan_text) <= 4000:
            await safe_edit(query, plan_text, reply_markup=plan_menu())
        else:
            await safe_edit(query, plan_text[:4000])
            await query.message.reply_text(plan_text[4000:], reply_markup=plan_menu())
        return

    if data == "show_today_plan":
        await query.answer()

        if not has_study_plan(user.id):
            await safe_edit(query, "⚠️ اعمل خطتك الأول!", reply_markup=plan_menu())
            return

        plan = get_study_plan(user.id)

        from datetime import datetime as dt
        days_ar = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
        today_name = days_ar[dt.now().weekday()]

        try:
            prompt = f"""من الخطة دي، استخرجلي يوم {today_name} بس:

{plan['plan_text']}

اكتب بالعربي بإيجاز."""
            today_plan = ai_generate(prompt, max_tokens=1000)
            today_plan = clean_text(today_plan)
        except Exception as e:
            today_plan = f"❌ حصل خطأ: {str(e)}"

        await safe_edit(query, today_plan, reply_markup=plan_menu())
        return

    if data == "regenerate_plan":
        await query.answer()

        if not has_analysis(user.id):
            await safe_edit(query, "⚠️ محتاج تحليل!", reply_markup=plan_needs_analysis_menu())
            return

        await safe_edit(query, "⏳ *جاري تجديد الخطة...*")

        analysis = get_analysis(user.id)
        subjects = get_user_subjects(user.id)
        college = get_user_college(user.id)

        try:
            plan_text = generate_study_plan(analysis, subjects, college)
            plan_text = clean_text(plan_text)
            save_study_plan(user.id, plan_text)
        except Exception as e:
            plan_text = f"❌ حصل خطأ: {str(e)}"

        if len(plan_text) <= 4000:
            await safe_edit(query, plan_text, reply_markup=plan_menu())
        else:
            await safe_edit(query, plan_text[:4000])
            await query.message.reply_text(plan_text[4000:], reply_markup=plan_menu())
        return


# ===== معالجة الأزرار العامة =====
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user = query.from_user

    if data == "skip_subjects":
        await safe_edit(query, "👍 تمام!")
        context.user_data["awaiting_college"] = True
        await update.effective_chat.send_message("🎓 *في أي كلية بتدرس؟*\n\nاكتب اسم كليتك:")
        return

    if data == "enter_subjects":
        await safe_edit(query, "📚 *اكتب موادك*\n\nكل مادة في سطر:")
        context.user_data["awaiting_subjects"] = True
        return

    if data == "my_subjects":
        subjects = get_user_subjects(user.id)
        if not subjects:
            text = "📚 *موادي*\n\nلسه مسجلتش مواد."
        else:
            subjects_list = "\n".join([f"{i+1}. {s}" for i, s in enumerate(subjects)])
            text = f"📚 *موادي ({len(subjects)}):*\n\n{subjects_list}"
        await safe_edit(query, text, reply_markup=subjects_menu())
        return

    if data == "add_subject":
        await safe_edit(query, "➕ *ضيف مادة*\n\nاكتب اسم المادة:")
        context.user_data["awaiting_subjects"] = True
        return

    if data == "list_subjects":
        subjects = get_user_subjects(user.id)
        if not subjects:
            text = "📚 لسه مفيش مواد."
        else:
            subjects_list = "\n".join([f"{i+1}. {s}" for i, s in enumerate(subjects)])
            text = f"📚 *موادي ({len(subjects)}):*\n\n{subjects_list}"
        await safe_edit(query, text, reply_markup=subjects_menu())
        return

    if data == "delete_subject_menu":
        subjects = get_user_subjects(user.id)
        if not subjects:
            await safe_edit(query, "📚 لسه مفيش مواد.", reply_markup=subjects_menu())
            return
        keyboard = []
        for subject in subjects:
            keyboard.append([InlineKeyboardButton(f"🗑️ {subject}", callback_data=f"del_subj_{subject}")])
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="my_subjects")])
        await safe_edit(query, "🗑️ *اختار المادة:*", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data.startswith("del_subj_"):
        subject_name = data.replace("del_subj_", "")
        delete_subject(user.id, subject_name)
        await safe_edit(query, f"✅ تم حذف: {subject_name}", reply_markup=subjects_menu())
        return

    if data == "clear_all_subjects":
        clear_user_subjects(user.id)
        await safe_edit(query, "✅ تم مسح كل المواد.", reply_markup=subjects_menu())
        return

    if data == "show_my_plan":
        if not has_analysis(user.id):
            await safe_edit(query, "⚠️ محتاج تحليل الأول!", reply_markup=plan_needs_analysis_menu())
            return
        await safe_edit(query, "📊 *خطتك المخصصة*", reply_markup=plan_menu())
        return

    if data == "back_home":
        await safe_edit(query, "🏠 *القائمة الرئيسية*\n\nاختار من الأزرار تحت 👇")
        return

    if data == "upload_pdf":
        await safe_edit(query, "📄 *ارفع ملف PDF*\n\nابعتلي الملف.")
        return

    if data == "upload_image":
        await safe_edit(query, "📸 *قريب إن شاء الله* 🚧")
        return

    if data == "quiz_from_pdf":
        await safe_edit(query, "🎯 *كويز من PDF*\n\nارفع PDF الأول.")
        return

    if data in ["quiz_random", "quiz_subject", "quiz_daily"]:
        await safe_edit(query, "🎯 *قريب إن شاء الله* 🚧")
        return

    if data == "explain_concept":
        await safe_edit(query, "💡 *اشرحلي مفهوم*\n\nابعتلي اسم المفهوم.")
        context.user_data["awaiting_explanation"] = "concept"
        return

    if data == "explain_term":
        await safe_edit(query, "🔤 *اشرحلي مصطلح*\n\nابعتلي المصطلح.")
        context.user_data["awaiting_explanation"] = "term"
        return

    if data == "solve_problem":
        await safe_edit(query, "🧮 *حل مسألة*\n\nابعتلي المسألة.")
        context.user_data["awaiting_explanation"] = "problem"
        return

    if data == "translate_text":
        await safe_edit(query, "🌍 *ترجمة نص*\n\nابعتلي النص.")
        return

    if data == "translate_file":
        await safe_edit(query, "📄 *ترجمة ملف*\n\nارفع الملف.")
        return

    if data == "summarize_text":
        await safe_edit(query, "📝 *تلخيص نص*\n\nابعتلي النص.")
        return

    if data == "summarize_file":
        await safe_edit(query, "📄 *تلخيص ملف*\n\nارفع الملف.")
        return

    if data == "account_info":
        plan = get_user_plan(user.id)
        allowed, remaining = check_limit(user.id)
        points, level = get_user_points(user.id)
        level_info = get_level_info(points)
        college = get_user_college(user.id)

        plan_names = {"free": "🆓 مجاني", "premium": "⭐ مميز", "admin": "👑 أدمن"}

        text = (
            f"👤 *بياناتك*\n\n"
            f"📛 الاسم: {user.first_name}\n"
            f"🆔 الـ ID: {user.id}\n"
            f"📊 الحساب: {plan_names.get(plan, 'مجاني')}\n"
            f"💎 النقاط: {points}\n"
            f"🏆 المستوى: {level_info['name']}\n"
            f"✅ متبقي اليوم: {remaining}\n"
            f"🎓 الكلية: {college or 'لسه'}\n"
        )
        await safe_edit(query, text)
        return

    if data == "account_stats":
        pomo = get_pomodoro_stats(user.id, days=7)
        points, level = get_user_points(user.id)

        text = (
            f"📊 *إحصائياتك*\n\n"
            f"💎 النقاط: {points}\n"
            f"⏱️ جلسات Pomodoro (7 أيام): {pomo['sessions']}\n"
            f"⏰ دقائق المذاكرة: {pomo['minutes']}\n"
        )
        await safe_edit(query, text)
        return

    if data == "account_badges":
        await safe_edit(query, "🎖️ *إنجازاتك*\n\n_قريب إن شاء الله_ 🚧")
        return

    if data == "account_upgrade":
        await safe_edit(
            query,
            f"💎 *ترقية الحساب*\n\nللترقية تواصل مع:\n👨‍💻 {DEVELOPER_NAME}\n📱 {DEVELOPER_USERNAME}"
        )
        return

    if data == "about":
        await safe_edit(query, ABOUT_MESSAGE)
        return

    if data == "admin_stats" and user.id in ADMIN_IDS:
        stats = get_detailed_stats()

        text = (
            f"📊 *إحصائيات البوت*\n\n"
            f"👥 المستخدمين: {stats['total_users']}\n"
            f"🆕 نشطين النهاردة: {stats['active_today']}\n"
            f"⭐ Premium: {stats['premium_users']}\n"
            f"👑 Admins: {stats['admin_users']}\n"
            f"📨 إجمالي الطلبات: {stats['total_requests']}\n"
            f"💎 إجمالي النقاط: {stats['total_points']}\n\n"
        )

        if stats["top_users"]:
            text += "🏆 *أعلى 5 طلاب:*\n"
            for i, (name, points) in enumerate(stats["top_users"]):
                text += f"{i+1}. {name or 'طالب'} — {points} 💎\n"

        await safe_edit(query, text, reply_markup=admin_panel_menu())
        return

    if data == "admin_users" and user.id in ADMIN_IDS:
        users = get_all_users(20)

        if not users:
            await safe_edit(query, "👥 *آخر 20 مستخدم:*\n\nلسه مفيش 🚧", reply_markup=admin_panel_menu())
            return

        mid = len(users) // 2
        part1 = users[:mid] if mid > 0 else users
        part2 = users[mid:] if mid > 0 else []

        text1 = f"👥 *آخر {len(users)} مستخدم*\n(الجزء الأول من {len(part1)})\n\n"
        for u_id, first_name, username, points, level, plan, last_used in part1:
            plan_emoji = {"free": "🆓", "premium": "⭐", "admin": "👑", "banned": "🚫"}.get(plan, "🆓")
            text1 += f"{plan_emoji} *{first_name or 'مستخدم'}* — {points} 💎\n"
            text1 += f"   🆔 {u_id}\n\n"

        await safe_edit(query, text1, reply_markup=admin_panel_menu())

        if part2:
            text2 = f"(الجزء التاني من {len(part2)})\n\n"
            for u_id, first_name, username, points, level, plan, last_used in part2:
                plan_emoji = {"free": "🆓", "premium": "⭐", "admin": "👑", "banned": "🚫"}.get(plan, "🆓")
                text2 += f"{plan_emoji} *{first_name or 'مستخدم'}* — {points} 💎\n"
                text2 += f"   🆔 {u_id}\n\n"
            await update.effective_chat.send_message(text2)

        return

    if data == "admin_broadcast" and user.id in ADMIN_IDS:
        await safe_edit(query, "📢 *بث رسالة*\n\n_قريب إن شاء الله_ 🚧", reply_markup=admin_panel_menu())
        return


# ===== عرض الأسئلة =====
async def show_next_question(query, context, step):
    user = query.from_user

    questions = {
        1: ("⏰ *إنت بتذاكر إمتى؟*", analysis_q1_time()),
        2: ("⏱️ *بتقدر تركز كام دقيقة؟*", analysis_q2_duration()),
        3: ("🧠 *بتفهم إزاي أكتر؟*", analysis_q3_style()),
        5: ("🎯 *هدفك من المذاكرة؟*", analysis_q5_goal()),
        6: ("📅 *امتحاناتك إمتى؟*", analysis_q6_exams()),
    }

    if step == 4:
        subjects = get_user_subjects(user.id)
        text = "😰 *إيه أصعب مادة عليك؟*"
        markup = analysis_q4_hard_subject(subjects)
        await safe_edit(query, f"📊 *سؤال 4 من 6*\n\n{text}\n\n━━━━━━━━━━━━━━━", reply_markup=markup)
        return

    if step > 6:
        await finish_analysis(query, context, user)
        return

    if step in questions:
        question_text, markup = questions[step]
        await safe_edit(
            query,
            f"📊 *سؤال {step} من 6*\n\n{question_text}\n\n━━━━━━━━━━━━━━━",
            reply_markup=markup
        )
        return


# ===== إنهاء التحليل =====
async def finish_analysis(query, context, user):
    await safe_edit(query, "⏳ *جاري تحليل إجاباتك...*")

    answers = context.user_data.get("analysis_answers", {})

    study_time = answers.get("q1", "skip")
    focus_duration = answers.get("q2", "skip")
    learning_style = answers.get("q3", "skip")
    hard_subject = answers.get("q4", "skip")
    goal = answers.get("q5", "skip")
    exam_timing = answers.get("q6", "skip")

    if hard_subject == "skip":
        subjects = get_user_subjects(user.id)
        if subjects:
            hard_subject = subjects[0]

    try:
        prompt = f"""
إنت "ذاكر" - مدرب دراسي.

المستخدم جاوب:
1. وقت المذاكرة: {get_subject_display(study_time)}
2. مدة التركيز: {get_subject_display(focus_duration)}
3. نمط التعلم: {get_subject_display(learning_style)}
4. أصعب مادة: {hard_subject}
5. الهدف: {get_subject_display(goal)}
6. الامتحانات: {get_subject_display(exam_timing)}

طلع تقرير بالعربي:

🧠 نمطك الدراسي:
- (وصف)

⚡ نقاط قوتك:
• (3 نقاط)

⚠️ نقاط ضعفك:
• (3 نقاط)

💡 نصيحة مخصصة:
• (2-3 نصائح)
"""

        analysis_result = ai_generate(prompt, max_tokens=1500)
        analysis_result = clean_text(analysis_result)

    except Exception as e:
        analysis_result = "حصل خطأ في التحليل."
        print(f"Error: {e}")

    save_analysis(
        user.id,
        study_time, focus_duration, learning_style,
        hard_subject, goal, exam_timing, analysis_result
    )

    add_points(user.id, POINTS_REWARDS["analysis_done"])
    context.user_data["in_analysis"] = False

    full_text = (
        f"🎉 *تحليلك جاهز!*\n\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"📊 *إجاباتك:*\n\n"
        f"🌙 وقت مذاكرتك: {get_subject_display(study_time)}\n"
        f"⏱️ تركيزك: {get_subject_display(focus_duration)}\n"
        f"🧠 نمط تعلمك: {get_subject_display(learning_style)}\n"
        f"📚 أصعب مادة: {hard_subject}\n"
        f"🎯 هدفك: {get_subject_display(goal)}\n"
        f"📅 امتحاناتك: {get_subject_display(exam_timing)}\n\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"{analysis_result}\n\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"💎 *كسبت {POINTS_REWARDS['analysis_done']} نقطة!*"
    )

    if len(full_text) <= 4000:
        await safe_edit(query, full_text, reply_markup=analysis_result_menu())
    else:
        await safe_edit(query, full_text[:4000])
        await query.message.reply_text(full_text[4000:], reply_markup=analysis_result_menu())


# ===== معالجة PDF =====
async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    document = update.message.document

    get_or_create_user(user.id, user.username, user.first_name)

    allowed, remaining = check_limit(user.id)
    if not allowed:
        await update.message.reply_text(f"⚠️ وصلت للحد اليومي!\n\n💎 تواصل مع {DEVELOPER_USERNAME}")
        return

    if not document.file_name.lower().endswith('.pdf'):
        await update.message.reply_text("⚠️ بس ملفات PDF مسموحة.")
        return

    waiting = await update.message.reply_text("📄 جاري تحميل الملف...")

    pdf_path = f"temp_{user.id}.pdf"

    try:
        file = await document.get_file()
        await file.download_to_drive(pdf_path)

        await waiting.edit_text("📖 جاري قراءة المحتوى...")
        pdf_text = process_pdf(pdf_path)

        if not pdf_text.strip():
            await waiting.edit_text("❌ الملف فاضي أو مش مقروء.")
            return

        context.user_data["pdf_text"] = pdf_text
        context.user_data["pdf_file_name"] = document.file_name
        context.user_data["pdf_page_count"] = len(pdf_text.split("\n")) // 40

        clear_pdf_analysis(user.id)
        context.user_data.pop("chapters", None)
        context.user_data.pop("quick_summary", None)

        await waiting.edit_text(
            f"✅ *تم تحميل الملف!*\n\n"
            f"📄 *الملف:* {document.file_name}\n"
            f"📝 *حجم المحتوى:* {len(pdf_text)} حرف\n\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"🎯 *إيه اللي عايزه؟*",
            reply_markup=quick_actions_menu()
        )

        if os.path.exists(pdf_path):
            os.remove(pdf_path)

    except Exception as e:
        await waiting.edit_text(f"❌ حصل خطأ: {str(e)}")
        if os.path.exists(pdf_path):
            os.remove(pdf_path)


# ===== معالجة الرسائل النصية =====
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    get_or_create_user(user.id, user.username, user.first_name)

    # ===== سؤال عن PDF =====
    if context.user_data.get("awaiting_pdf_question"):
        context.user_data["awaiting_pdf_question"] = False

        pdf_text = context.user_data.get("pdf_text", "")
        if not pdf_text:
            analysis = get_pdf_analysis(user.id)
            if analysis:
                pdf_text = analysis["pdf_text"]

        if not pdf_text:
            await update.message.reply_text("⚠️ مفيش ملف محفوظ.")
            return

        waiting = await update.message.reply_text("💬 جاري البحث...")

        try:
            if len(pdf_text) > 15000:
                pdf_text = pdf_text[:15000] + "..."

            prompt = f"""إنت مساعد طالب جامعي.

المحتوى:
{pdf_text}

━━━━━━━━━━━━━━━

سؤال الطالب: {text}

جاوب بالعربي. لو المعلومة مش موجودة، قول "المعلومة دي مش موجودة في الملف"."""

            response = ai_generate(prompt, max_tokens=1500)
            response = clean_text(response)

            await waiting.edit_text(
                f"💬 *سؤالك:* {text}\n\n"
                f"━━━━━━━━━━━━━━━\n\n"
                f"{response}",
                reply_markup=quick_actions_menu()
            )

        except Exception as e:
            await waiting.edit_text(f"❌ حصل خطأ: {str(e)}")
        return

    # ===== إدخال المواد =====
    if context.user_data.get("awaiting_subjects"):
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        if not lines:
            await update.message.reply_text("⚠️ اكتب مادة واحدة على الأقل.")
            return

        added = []
        for subject in lines:
            if add_subject(user.id, subject):
                added.append(subject)

        context.user_data["awaiting_subjects"] = False

        if added:
            added_text = "\n".join([f"✅ {s}" for s in added])
            await update.message.reply_text(
                f"🎉 *تمام! حفظت موادك:*\n\n{added_text}\n\n"
                f"🎓 *في أي كلية بتدرس؟*\nاكتب اسم كليتك:"
            )
        else:
            await update.message.reply_text(
                "⚠️ المواد دي موجودة بالفعل.\n\n🎓 *في أي كلية بتدرس؟*"
            )
        context.user_data["awaiting_college"] = True
        return

    # ===== إدخال الكلية =====
    if context.user_data.get("awaiting_college"):
        college = text.strip()
        context.user_data["awaiting_college"] = False
        set_user_college(user.id, college)
        complete_onboarding(user.id)

        await update.message.reply_text(
            f"🎉 *تمام! كلية: {college}*\n\nابدأ من الأزرار تحت 👇",
            reply_markup=main_menu(is_admin=(user.id in ADMIN_IDS))
        )
        return

    # ===== اشرحلي =====
    if context.user_data.get("awaiting_explanation"):
        explanation_type = context.user_data.pop("awaiting_explanation")

        waiting = await update.message.reply_text("💡 جاري الشرح...")

        try:
            if explanation_type == "concept":
                prompt = f"اشرحلي المفهوم ده بالعربي بالتفصيل، مع أمثلة:\n\n{text}"
            elif explanation_type == "term":
                prompt = f"اشرحلي المصطلح ده بالعربي:\n\n{text}\n\nاكتب:\n🔤 المصطلح (English)\n📖 المعنى\n💡 مثال"
            else:
                prompt = f"حل المسألة دي بالعربي خطوة بخطوة:\n\n{text}"

            response = ai_generate(prompt, max_tokens=2500)
            response = clean_text(response)
            await waiting.edit_text(response)

        except Exception as e:
            await waiting.edit_text(f"❌ حصل خطأ: {str(e)}")
        return

    # ===== المعالجة العادية =====
    allowed, remaining = check_limit(user.id)
    if not allowed:
        await update.message.reply_text(f"⚠️ وصلت للحد اليومي!\n\n💎 تواصل مع {DEVELOPER_USERNAME}")
        return

    waiting = await update.message.reply_text("⏳ جاري المعالجة...")

    try:
        translation = translate_text(text, "الإنجليزية")
        summary = summarize_text(text)

        result = (
            f"📝 النص الأصلي:\n{text}\n\n"
            f"🌍 الترجمة:\n{translation}\n\n"
            f"📋 التلخيص:\n{summary}\n\n"
            f"━━━━━━━━━━━━━━━\n"
            f"👤 متبقي: {remaining - 1} استخدام"
        )

        increment_usage(user.id, POINTS_REWARDS["text_analysis"])
        await waiting.edit_text(result)

    except Exception as e:
        await waiting.edit_text(f"❌ حصل خطأ: {str(e)}")


# ===== معالجة الأزرار Reply =====
async def handle_reply_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.effective_user

    if context.user_data.get("awaiting_subjects") or context.user_data.get("awaiting_college"):
        await handle_message(update, context)
        return

    if context.user_data.get("awaiting_pdf_question") or context.user_data.get("awaiting_explanation"):
        await handle_message(update, context)
        return

    if context.user_data.get("in_analysis"):
        return

    if text == "📄 تحليل PDF":
        await update.message.reply_text("📄 *ارفع ملف PDF*\n\nابعتلي الملف.")
        return

    if text == "📸 صورة":
        await update.message.reply_text("📸 *قريب إن شاء الله* 🚧")
        return

    if text == "🎯 كويز":
        await update.message.reply_text("🎯 *اختار:*", reply_markup=quiz_menu())
        return

    if text == "📚 شرح":
        await update.message.reply_text("📚 *اختار:*", reply_markup=explain_menu())
        return

    if text == "🌍 ترجمة":
        await update.message.reply_text("🌍 *اختار:*", reply_markup=translate_menu())
        return

    if text == "📝 تلخيص":
        await update.message.reply_text("📝 *اختار:*", reply_markup=summarize_menu())
        return

    if text == "🏆 حسابي":
        await update.message.reply_text("🏆 *حسابك:*", reply_markup=account_menu())
        return

    if text == "🎁 هدية يومية":
        await daily_command(update, context)
        return

    if text == "💎 نقاطي":
        await points_command(update, context)
        return

    if text == "🏆 المتصدرين":
        await leaderboard_command(update, context)
        return

    if text == "👥 دعوة أصدقاء":
        await invite_command(update, context)
        return

    if text == "📚 موادي":
        await subjects_command(update, context)
        return

    if text == "🧠 حللني":
        if has_analysis(user.id):
            await analysis_command(update, context)
        else:
            context.user_data["in_analysis"] = True
            context.user_data["analysis_step"] = 1
            context.user_data["analysis_answers"] = {}

            await update.message.reply_text(
                "📊 *سؤال 1 من 6*\n\n⏰ *إنت بتذاكر إمتى؟*\n\n━━━━━━━━━━━━━━━",
                reply_markup=analysis_q1_time()
            )
        return

    if text == "📊 خطتي":
        if not has_analysis(user.id):
            await update.message.reply_text(
                "⚠️ *لسه محتاج تحليل الأول!*",
                reply_markup=plan_needs_analysis_menu()
            )
            return
        await update.message.reply_text("📊 *خطتك المخصصة*\n\nاختار:", reply_markup=plan_menu())
        return

    if text == "⏱️ ذاكر معايا":
        if not has_subjects(user.id):
            await update.message.reply_text("⚠️ *ضيف موادك الأول!*", reply_markup=subjects_menu())
            return
        await update.message.reply_text("⏱️ *Pomodoro*\n\nاختار:", reply_markup=pomodoro_start_menu())
        return

    if text == "🏆 إنجازاتي":
        await update.message.reply_text("🏆 *قريب إن شاء الله* 🚧")
        return

    if text == "🎛️ لوحة التحكم":
        if user.id in ADMIN_IDS:
            await update.message.reply_text("🎛️ *لوحة التحكم*", reply_markup=admin_panel_menu())
        return

    await handle_message(update, context)


# ===== تشغيل =====
def main():
    init_db()

    request = HTTPXRequest(
        connection_pool_size=8,
        connect_timeout=60.0,
        read_timeout=120.0,
        write_timeout=120.0,
    )

    app = Application.builder().token(TOKEN).request(request).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("myplan", myplan_command))
    app.add_handler(CommandHandler("points", points_command))
    app.add_handler(CommandHandler("daily", daily_command))
    app.add_handler(CommandHandler("leaderboard", leaderboard_command))
    app.add_handler(CommandHandler("invite", invite_command))
    app.add_handler(CommandHandler("subjects", subjects_command))
    app.add_handler(CommandHandler("analysis", analysis_command))

    app.add_handler(CallbackQueryHandler(handle_analysis_buttons, pattern="^(analysis_|ans_)"))
    app.add_handler(CallbackQueryHandler(handle_pdf_buttons, pattern="^(pdf_|quick_|full_|ask_pdf|download_|show_chapters|chapter_|explain_|quiz_this)"))
    app.add_handler(CallbackQueryHandler(handle_pomodoro_buttons, pattern="^pomodoro_|^start_pomodoro"))
    app.add_handler(CallbackQueryHandler(handle_plan_buttons, pattern="^(show_weekly_plan|show_today_plan|regenerate_plan)$"))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reply_buttons))

    print(f"✅ {BOT_NAME} v{BOT_VERSION} شغال!")
    print(f"👨‍💻 المطور: {DEVELOPER_NAME}")
    print(f"🤖 Groq Model: {GROQ_MODEL}")
    print("اضغط Ctrl+C للإيقاف.")
    app.run_polling()


if __name__ == "__main__":
    main()