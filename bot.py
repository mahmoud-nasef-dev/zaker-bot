import os
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
    set_user_college, get_user_college
)
from keyboards import (
    main_menu, pdf_menu, quiz_menu, explain_menu,
    translate_menu, summarize_menu, account_menu,
    back_button, points_menu, analysis_options_menu,
    admin_panel_menu, admin_user_actions,
    skip_subjects_button, subjects_menu
)

# ===== الإعدادات =====
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-3.6-flash")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


# ===== دوال AI =====
def translate_text(text, target_language="الإنجليزية"):
    prompt = f"إنت مترجم محترف. ترجم النص ده لـ {target_language} فقط، بدون أي إضافات:\n\n{text}"
    response = model.generate_content(prompt)
    return response.text


def summarize_text(text):
    prompt = f"لخص النص ده في 3 نقاط بس، بالعربي:\n\n{text}"
    response = model.generate_content(prompt)
    return response.text


def process_pdf(file_path):
    """بيقرا ملف PDF وبيرجع النص بتاعه"""
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text


def analyze_pdf_content(text, analysis_type="summary", user_subjects=None, user_college=None):
    """بيحلل محتوى PDF حسب النوع المطلوب"""
    if len(text) > 15000:
        text = text[:15000] + "..."

    # نبني سياق المواد والكلية
    context_parts = []
    context_parts.append("إنت مساعد طالب جامعي.")
    
    if user_college:
        context_parts.append(f"الطالب في كلية: {user_college}.")
    
    if user_subjects:
        subjects_str = ", ".join(user_subjects)
        context_parts.append(f"مواد الطالب: {subjects_str}.")
        context_parts.append("خلي أمثلتك وشرحك يناسب الكلية والمواد دي.")
    else:
        context_parts.append("إنت مساعد طالب جامعي في أي كلية أو مادة.")
    
    subjects_context = "\n".join(context_parts)

    prompts = {
        "summary": f"""{subjects_context}
المحتوى ده من محاضرة بالإنجليزي.

اعملي **ملخص سريع بالعربي** في 5-7 نقاط أساسية بس.
خليك مختصر ومباشر.

المحتوى:
{text}
""",
        "explanation": f"""{subjects_context}
المحتوى ده من محاضرة بالإنجليزي.

اعملي **شرح تفصيلي بالعربي** للمحتوى كله، بشرط:

1. اشرح **كل نقطة** بالتفصيل
2. ادي **أمثلة** على كل نقطة
3. اشرح **المصطلحات** جوا السياق
4. نظّم الشرح في **أجزاء صغيرة** (كل جزء 3-4 أسطر)

المحتوى:
{text}
""",
        "terms": f"""{subjects_context}
المحتوى ده من محاضرة بالإنجليزي.

اعملي **قائمة المصطلحات المهمة** بالشكل ده:

🔤 **المصطلح**
📖 المعنى بالعربي
💡 مثال

خليها 10-15 مصطلح أساسي.

المحتوى:
{text}
""",
        "quiz": f"""{subjects_context}
المحتوى ده من محاضرة بالإنجليزي.

اعملي **5 أسئلة اختيارات** على المحتوى، بالشكل ده بالظبط:

**السؤال 1:**
نص السؤال؟
أ) خيار 1
ب) خيار 2
ج) خيار 3
د) خيار 4
✅ الإجابة الصحيحة: (أ/ب/ج/د)

**السؤال 2:**
...

المحتوى:
{text}
""",
        "examples": f"""{subjects_context}
المحتوى ده من محاضرة بالإنجليزي.

اعملي **5 أمثلة عملية من الحياة الواقعية** على المفاهيم اللي في المحتوى.
كل مثال:
🎯 المفهوم
💡 المثال
📝 الشرح

المحتوى:
{text}
""",
        "problems": f"""{subjects_context}
المحتوى ده من محاضرة بالإنجليزي.

اعملي **5 تمارين/مسائل عملية** على المحتوى.
كل مسألة:
❓ السؤال
📝 الحل خطوة بخطوة

المحتوى:
{text}
""",
    }

    prompt = prompts.get(analysis_type, prompts["summary"])
    response = model.generate_content(prompt)
    return response.text


def clean_text(text):
    """بتنضف النص من علامات Markdown"""
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


# ===== دوال النقاط =====
def format_level_bar(points, level_info):
    """بيرسم شريط تقدم المستوى"""
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

    # تحقق من المواد
    if not has_subjects(user.id):
        await update.message.reply_text(
            f"أهلاً *{user.first_name}*! 👋\n\n"
            f"🎓 إنت في *ذاكر* - مساعدك الدراسي\n\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"قبل ما نبدأ، عايز أعرف عنك شوية:\n\n"
            f"📚 *اكتب المواد اللي بتدرسها*\n"
            f"(اكتب كل مادة في سطر)\n\n"
            f"مثال:\n"
            f"`Algorithms`\n"
            f"`Database`\n"
            f"`Machine Learning`\n\n"
            f"_أو اختار من الأزرار تحت_ 👇",
            parse_mode="Markdown",
            reply_markup=skip_subjects_button()
        )
        return

    # تحقق من الكلية
    user_college = get_user_college(user.id)
    if not user_college:
        context.user_data["awaiting_college"] = True
        await update.message.reply_text(
            f"📚 تمام! موادي محفوظة ✅\n\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"🎓 عايز أعرف *إنت في أي كلية*:\n\n"
            f"اكتب اسم كليتك (مثال: حاسبات، طب، هندسة، تجارة، آداب، حقوق، علوم...)",
            parse_mode="Markdown"
        )
        return

    # ترحيب عادي
    plan = get_user_plan(user.id)
    allowed, remaining = check_limit(user.id)
    points, level = get_user_points(user.id)
    level_info = get_level_info(points)
    subjects = get_user_subjects(user.id)

    plan_names = {
        "free": "🆓 مجاني",
        "premium": "⭐ مميز",
        "admin": "👑 أدمن",
    }

    subjects_text = "، ".join(subjects[:3]) if subjects else "مفيش"
    if len(subjects) > 3:
        subjects_text += f" + {len(subjects)-3}"

    welcome = (
        f"أهلاً *{user.first_name}*! 👋\n\n"
        f"🎓 *ذاكر* - مساعدك الدراسي\n\n"
        f"💎 *نقاطك:* {points}\n"
        f"🏆 *مستواك:* {level_info['name']}\n"
        f"👤 *حسابك:* {plan_names.get(plan, 'مجاني')}\n"
        f"📊 *متبقي اليوم:* {remaining} استخدام\n"
        f"🎓 *كليتك:* {user_college}\n"
        f"📚 *موادك:* {subjects_text}\n\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"*اختار من الأزرار تحت* 👇"
    )

    is_admin = user.id in ADMIN_IDS

    await update.message.reply_text(
        welcome,
        parse_mode="Markdown",
        reply_markup=main_menu(is_admin=is_admin)
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📚 *الأوامر المتاحة:*\n\n"
        "/start - البداية\n"
        "/help - مساعدة\n"
        "/about - عن ذاكر\n"
        "/myplan - خطتك الحالية\n"
        "/points - نقاطك ومستواك\n"
        "/daily - هدية يومية\n"
        "/leaderboard - المتصدرين\n"
        "/invite - دعوة أصدقاء\n"
        "/subjects - موادي"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(ABOUT_MESSAGE, parse_mode="Markdown")


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

    await update.message.reply_text(text, parse_mode="Markdown")


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
        f"`{bar}`\n\n"
        f"🎯 عايز نقاط أكتر؟\n"
        f"• استخدم البوت\n"
        f"• استلم هديتك اليومية\n"
        f"• ادعي أصحابك"
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=points_menu()
    )


async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_or_create_user(user.id, user.username, user.first_name)

    result = claim_daily_gift(user.id)

    if not result["success"]:
        await update.message.reply_text(
            f"⚠️ {result['message']}\n\n🔔 متنساش ترجع تاني!",
        )
        return

    text = f"🎉 *مبروك!*\n\n💎 كسبت: *{result['points']}* نقطة\n"

    if result["bonus"] > 0:
        text += f"🎁 بونص السلسلة: *+{result['bonus']}* نقطة\n"

    text += (
        f"\n🔥 *سلسلتك:* {result['streak']} يوم\n"
        f"📊 *إجمالي نقاطك:* {result['new_points']}\n"
        f"🏆 *مستواك:* {result['level']['name']}"
    )

    await update.message.reply_text(text, parse_mode="Markdown")


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

    await update.message.reply_text(text, parse_mode="Markdown")


async def invite_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_or_create_user(user.id, user.username, user.first_name)

    bot_username = BOT_USERNAME.replace("@", "")
    invite_link = f"https://t.me/{bot_username}?start=invite_{user.id}"

    text = (
        f"👥 *دعوة الأصدقاء*\n\n"
        f"كل صاحب يدخل من لينكك = *20 نقطة* 💎\n\n"
        f"🔗 *لينكك الخاص:*\n"
        f"`{invite_link}`\n\n"
        f"📤 انسخ اللينك وابعته لأصحابك!"
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("📤 مشاركة", url=f"https://t.me/share/url?url={invite_link}")
        ]])
    )


async def subjects_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_or_create_user(user.id, user.username, user.first_name)

    subjects = get_user_subjects(user.id)

    if not subjects:
        text = (
            "📚 *موادك*\n\n"
            "لسه مسجلتش مواد.\n\n"
            "اختار من الأزرار:"
        )
    else:
        subjects_list = "\n".join([f"{i+1}. {s}" for i, s in enumerate(subjects)])
        text = (
            f"📚 *موادك ({len(subjects)}):*\n\n"
            f"{subjects_list}\n\n"
            f"عايز تعدل؟"
        )

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=subjects_menu()
    )


# ===== معالجة الأزرار Inline =====
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user = query.from_user

    # ===== المواد =====
    if data == "skip_subjects":
        await query.edit_message_text(
            "👍 تمام! تقدر تضيف موادك في أي وقت من:\n"
            "🏆 حسابي → 📚 موادي"
        )
        context.user_data["awaiting_college"] = True
        await update.effective_chat.send_message(
            "🎓 *في أي كلية بتدرس؟*\n\n"
            "اكتب اسم كليتك (مثال: حاسبات، طب، هندسة، تجارة، آداب...)",
            parse_mode="Markdown"
        )
        return

    if data == "enter_subjects":
        await query.edit_message_text(
            "📚 *اكتب موادك دلوقتي*\n\n"
            "اكتب كل مادة في سطر:\n"
            "`Algorithms`\n"
            "`Database`\n"
            "`Machine Learning`\n\n"
            "📝 مستنيك...",
            parse_mode="Markdown"
        )
        context.user_data["awaiting_subjects"] = True
        return

    if data == "my_subjects":
        subjects = get_user_subjects(user.id)
        if not subjects:
            text = "📚 *موادك*\n\nلسه مسجلتش مواد."
        else:
            subjects_list = "\n".join([f"{i+1}. {s}" for i, s in enumerate(subjects)])
            text = f"📚 *موادك ({len(subjects)}):*\n\n{subjects_list}"

        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=subjects_menu()
        )
        return

    if data == "add_subject":
        await query.edit_message_text(
            "➕ *ضيف مادة*\n\n"
            "اكتب اسم المادة (أو اكتبهم كلهم، كل مادة في سطر).\n\n"
            "📝 مستنيك...",
            parse_mode="Markdown"
        )
        context.user_data["awaiting_subjects"] = True
        return

    if data == "list_subjects":
        subjects = get_user_subjects(user.id)
        if not subjects:
            text = "📚 لسه مفيش مواد مسجلة."
        else:
            subjects_list = "\n".join([f"{i+1}. {s}" for i, s in enumerate(subjects)])
            text = f"📚 *موادك ({len(subjects)}):*\n\n{subjects_list}"

        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=subjects_menu()
        )
        return

    if data == "delete_subject_menu":
        subjects = get_user_subjects(user.id)
        if not subjects:
            await query.edit_message_text(
                "📚 لسه مفيش مواد.",
                reply_markup=subjects_menu()
            )
            return

        keyboard = []
        for subject in subjects:
            keyboard.append([
                InlineKeyboardButton(f"🗑️ {subject}", callback_data=f"del_subj_{subject}")
            ])
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="my_subjects")])

        await query.edit_message_text(
            "🗑️ *اختار المادة اللي عايز تحذفها:*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if data.startswith("del_subj_"):
        subject_name = data.replace("del_subj_", "")
        delete_subject(user.id, subject_name)
        await query.edit_message_text(
            f"✅ تم حذف: *{subject_name}*",
            parse_mode="Markdown",
            reply_markup=subjects_menu()
        )
        return

    if data == "clear_all_subjects":
        clear_user_subjects(user.id)
        await query.edit_message_text(
            "✅ تم مسح كل المواد.",
            reply_markup=subjects_menu()
        )
        return

    # ===== الأساسيات =====
    if data == "back_home":
        await query.edit_message_text(
            "🏠 *القائمة الرئيسية*\n\nاختار من الأزرار تحت 👇",
            parse_mode="Markdown"
        )
        return

    if data == "upload_pdf":
        await query.edit_message_text(
            "📄 *ارفع ملف PDF دلوقتي*\n\nابعتلي الملف وأنا هحلله.",
            parse_mode="Markdown"
        )
        return

    if data == "upload_image":
        await query.edit_message_text("📸 *ارفع صورة*\n\n_قريب إن شاء الله_ 🚧")
        return

    # ===== الكويز =====
    if data == "quiz_from_pdf":
        await query.edit_message_text("🎯 *كويز من PDF*\n\nارفع ملف PDF الأول.")
        return

    if data == "quiz_random":
        await query.edit_message_text("🎲 *كويز عشوائي*\n\n_قريب إن شاء الله_ 🚧")
        return

    if data == "quiz_subject":
        await query.edit_message_text("📚 *كويز من مادة*\n\n_قريب إن شاء الله_ 🚧")
        return

    if data == "quiz_daily":
        await query.edit_message_text("🎁 *الكويز اليومي*\n\n_قريب إن شاء الله_ 🚧")
        return

    # ===== الشرح =====
    if data == "explain_concept":
        await query.edit_message_text("💡 *اشرحلي مفهوم*\n\nابعتلي اسم المفهوم.")
        return

    if data == "explain_term":
        await query.edit_message_text("🔤 *اشرحلي مصطلح*\n\nابعتلي المصطلح.")
        return

    if data == "solve_problem":
        await query.edit_message_text("🧮 *حل مسألة*\n\nابعتلي المسألة.")
        return

    # ===== الترجمة =====
    if data == "translate_text":
        await query.edit_message_text("🌍 *ترجمة نص*\n\nابعتلي النص.")
        return

    if data == "translate_file":
        await query.edit_message_text("📄 *ترجمة ملف*\n\nارفع الملف.")
        return

    # ===== التلخيص =====
    if data == "summarize_text":
        await query.edit_message_text("📝 *تلخيص نص*\n\nابعتلي النص.")
        return

    if data == "summarize_file":
        await query.edit_message_text("📄 *تلخيص ملف*\n\nارفع الملف.")
        return

    # ===== الحساب =====
    if data == "account_info":
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

        subjects_text = "، ".join(subjects) if subjects else "لسه"

        text = (
            f"👤 *بياناتك*\n\n"
            f"📛 الاسم: {user.first_name}\n"
            f"🆔 الـ ID: `{user.id}`\n"
            f"📊 الحساب: {plan_names.get(plan, 'مجاني')}\n"
            f"💎 النقاط: {points}\n"
            f"🏆 المستوى: {level_info['name']}\n"
            f"✅ متبقي اليوم: {remaining} استخدام\n"
            f"🎓 الكلية: {college or 'لسه'}\n"
            f"📚 المواد: {subjects_text}\n"
        )

        await query.edit_message_text(text, parse_mode="Markdown")
        return

    if data == "account_stats":
        await query.edit_message_text("📊 *إحصائياتك*\n\n_قريب إن شاء الله_ 🚧")
        return

    if data == "account_badges":
        await query.edit_message_text("🎖️ *إنجازاتك*\n\n_قريب إن شاء الله_ 🚧")
        return

    if data == "account_upgrade":
        await query.edit_message_text(
            f"💎 *ترقية الحساب*\n\n"
            f"للترقية تواصل مع:\n"
            f"👨‍💻 {DEVELOPER_NAME}\n"
            f"📱 {DEVELOPER_USERNAME}",
            parse_mode="Markdown"
        )
        return

    if data == "about":
        await query.edit_message_text(ABOUT_MESSAGE, parse_mode="Markdown")
        return

    # ===== لوحة التحكم (Admin) =====
    if data == "admin_stats" and user.id in ADMIN_IDS:
        stats = get_detailed_stats()

        text = (
            f"📊 *إحصائيات البوت*\n\n"
            f"👥 *إجمالي المستخدمين:* {stats['total_users']}\n"
            f"🆕 *نشطين النهاردة:* {stats['active_today']}\n"
            f"⭐ *Premium:* {stats['premium_users']}\n"
            f"👑 *Admins:* {stats['admin_users']}\n"
            f"📨 *إجمالي الطلبات:* {stats['total_requests']}\n"
            f"💎 *إجمالي النقاط:* {stats['total_points']}\n\n"
        )

        if stats["top_users"]:
            text += "🏆 *أعلى 5 طلاب:*\n"
            for i, (name, points) in enumerate(stats["top_users"]):
                text += f"{i+1}. {name or 'طالب'} — {points} 💎\n"

        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=admin_panel_menu()
        )
        return

    if data == "admin_users" and user.id in ADMIN_IDS:
        users = get_all_users(20)

        if not users:
            await query.edit_message_text(
                "👥 *آخر 20 مستخدم:*\n\nلسه مفيش مستخدمين 🚧",
                parse_mode="Markdown",
                reply_markup=admin_panel_menu()
            )
            return

        mid = len(users) // 2
        part1 = users[:mid] if mid > 0 else users
        part2 = users[mid:] if mid > 0 else []

        text1 = f"👥 *آخر {len(users)} مستخدم*\n(الجزء الأول من {len(part1)})\n\n"
        for u_id, first_name, username, points, level, plan, last_used in part1:
            plan_emoji = {"free": "🆓", "premium": "⭐", "admin": "👑", "banned": "🚫"}.get(plan, "🆓")
            text1 += f"{plan_emoji} *{first_name or 'مستخدم'}* — {points} 💎\n"
            text1 += f"   🆔 `{u_id}`\n\n"

        await query.edit_message_text(
            text1,
            parse_mode="Markdown",
            reply_markup=admin_panel_menu()
        )

        if part2:
            text2 = f"(الجزء التاني من {len(part2)})\n\n"
            for u_id, first_name, username, points, level, plan, last_used in part2:
                plan_emoji = {"free": "🆓", "premium": "⭐", "admin": "👑", "banned": "🚫"}.get(plan, "🆓")
                text2 += f"{plan_emoji} *{first_name or 'مستخدم'}* — {points} 💎\n"
                text2 += f"   🆔 `{u_id}`\n\n"

            await update.effective_chat.send_message(text2, parse_mode="Markdown")

        return

    if data == "admin_broadcast" and user.id in ADMIN_IDS:
        await query.edit_message_text(
            "📢 *بث رسالة*\n\n"
            "ابعتلي الرسالة اللي عايز تبعتها لكل المستخدمين.\n\n"
            "_ملاحظة: الميزة دي قريب إن شاء الله_ 🚧",
            parse_mode="Markdown",
            reply_markup=admin_panel_menu()
        )
        return


# ===== معالجة اختيار نوع التحليل =====
async def handle_pdf_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if not data.startswith("analysis_"):
        await button_handler(update, context)
        return

    await query.answer()
    user = query.from_user

    analysis_type = data.replace("analysis_", "")

    pdf_text = context.user_data.get("pdf_text")
    if not pdf_text:
        await query.edit_message_text("⚠️ الملف مش موجود. ارفعه تاني.")
        return

    types = {
        "summary": "📝 الملخص",
        "explanation": "📚 الشرح التفصيلي",
        "terms": "🔤 المصطلحات",
        "quiz": "🎯 الكويز",
        "examples": "💡 الأمثلة",
        "problems": "🧮 المسائل",
    }
    type_name = types.get(analysis_type, "📝 التحليل")

    await query.edit_message_text(f"⏳ جاري إعداد {type_name}...")

    try:
        user_subjects = get_user_subjects(user.id)
        user_college = get_user_college(user.id)

        result = analyze_pdf_content(pdf_text, analysis_type, user_subjects, user_college)
        result = clean_text(result)

        full_text = f"{type_name}:\n\n{result}"

        if len(full_text) <= 4000:
            await query.edit_message_text(full_text)
        else:
            await query.edit_message_text(full_text[:4000])
            await update.effective_chat.send_message(full_text[4000:])

        increment_usage(user.id, POINTS_REWARDS["pdf_analysis"])

    except Exception as e:
        await query.edit_message_text(f"❌ حصل خطأ: {str(e)}")


# ===== معالجة PDF =====
async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    document = update.message.document

    get_or_create_user(user.id, user.username, user.first_name)

    allowed, remaining = check_limit(user.id)
    if not allowed:
        await update.message.reply_text(
            f"⚠️ وصلت للحد اليومي!\n\n💎 للترقية: تواصل مع {DEVELOPER_USERNAME}"
        )
        return

    if not document.file_name.lower().endswith('.pdf'):
        await update.message.reply_text("⚠️ بس ملفات PDF مسموحة.")
        return

    waiting = await update.message.reply_text("📄 جاري تحميل ومعالجة الملف...")

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

        await waiting.edit_text(
            f"✅ *تم تحميل الملف بنجاح!*\n\n"
            f"📝 *حجم المحتوى:* {len(pdf_text)} حرف\n\n"
            f"🎯 *اختار إيه اللي عايزه:*",
            parse_mode="Markdown",
            reply_markup=analysis_options_menu()
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
                f"━━━━━━━━━━━━━━━\n\n"
                f"🎓 *في أي كلية بتدرس؟*\n"
                f"اكتب اسم كليتك (مثال: حاسبات، طب، هندسة، تجارة، آداب...)",
                parse_mode="Markdown"
            )
            context.user_data["awaiting_college"] = True
        else:
            await update.message.reply_text(
                "⚠️ المواد دي موجودة بالفعل.",
                reply_markup=main_menu(is_admin=(user.id in ADMIN_IDS))
            )
        return

    # ===== إدخال الكلية =====
    if context.user_data.get("awaiting_college"):
        college = text.strip()
        context.user_data["awaiting_college"] = False
        set_user_college(user.id, college)

        await update.message.reply_text(
            f"🎉 *تمام! كلية: {college}*\n\n"
            f"دلوقتي عارف كل حاجة عنك 💪\n\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"ابدأ من الأزرار تحت 👇",
            parse_mode="Markdown",
            reply_markup=main_menu(is_admin=(user.id in ADMIN_IDS))
        )
        return

    # ===== المعالجة العادية =====
    allowed, remaining = check_limit(user.id)
    if not allowed:
        await update.message.reply_text(
            f"⚠️ وصلت للحد اليومي!\n\n💎 للترقية: تواصل مع {DEVELOPER_USERNAME}"
        )
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

    # ===== لو في عملية إدخال =====
    if context.user_data.get("awaiting_subjects") or context.user_data.get("awaiting_college"):
        await handle_message(update, context)
        return

    if text == "📄 تحليل PDF":
        await update.message.reply_text(
            "📄 *ارفع ملف PDF دلوقتي*\n\nابعتلي الملف وأنا هحلله.",
            parse_mode="Markdown"
        )
        return

    if text == "📸 صورة":
        await update.message.reply_text("📸 *ارفع صورة*\n\n_قريب إن شاء الله_ 🚧")
        return

    if text == "🎯 كويز":
        await update.message.reply_text(
            "🎯 *اختار نوع الكويز:*",
            parse_mode="Markdown",
            reply_markup=quiz_menu()
        )
        return

    if text == "📚 شرح":
        await update.message.reply_text(
            "📚 *اختار نوع الشرح:*",
            parse_mode="Markdown",
            reply_markup=explain_menu()
        )
        return

    if text == "🌍 ترجمة":
        await update.message.reply_text(
            "🌍 *اختار نوع الترجمة:*",
            parse_mode="Markdown",
            reply_markup=translate_menu()
        )
        return

    if text == "📝 تلخيص":
        await update.message.reply_text(
            "📝 *اختار نوع التلخيص:*",
            parse_mode="Markdown",
            reply_markup=summarize_menu()
        )
        return

    if text == "🏆 حسابي":
        await update.message.reply_text(
            "🏆 *حسابك:*",
            parse_mode="Markdown",
            reply_markup=account_menu()
        )
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

    if text == "🎛️ لوحة التحكم":
        if user.id in ADMIN_IDS:
            await update.message.reply_text(
                "🎛️ *لوحة التحكم*\n\nاختار من الأزرار:",
                parse_mode="Markdown",
                reply_markup=admin_panel_menu()
            )
        return

    await handle_message(update, context)


# ===== تشغيل =====
def main():
    init_db()

    request = HTTPXRequest(
        connection_pool_size=8,
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0,
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
    app.add_handler(CallbackQueryHandler(handle_pdf_options))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reply_buttons))

    print(f"✅ {BOT_NAME} v{BOT_VERSION} شغال!")
    print(f"👨‍💻 المطور: {DEVELOPER_NAME}")
    print("اضغط Ctrl+C للإيقاف.")
    app.run_polling()


if __name__ == "__main__":
    main()