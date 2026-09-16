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
    check_limit, get_user_plan, set_user_plan, get_stats,
    add_points, get_user_points, claim_daily_gift,
    get_daily_status, get_leaderboard, get_level_info,
       POINTS_REWARDS, LEVELS,
    get_all_users, get_user_details, get_detailed_stats,
    ban_user, unban_user, get_all_user_ids
)
from keyboards import (
    main_menu, pdf_menu, quiz_menu, explain_menu,
    translate_menu, summarize_menu, account_menu,
        admin_menu, back_button, points_menu, analysis_options_menu,
    admin_panel_menu, admin_user_actions
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


def analyze_pdf_content(text, analysis_type="summary"):
    """بيحلل محتوى PDF حسب النوع المطلوب"""
    if len(text) > 15000:
        text = text[:15000] + "..."

    prompts = {
        "summary": f"""إنت مساعد طالب جامعي في كلية الحاسبات والذكاء الاصطناعي.
المحتوى ده من محاضرة بالإنجليزي.

اعملي **ملخص سريع بالعربي** في 5-7 نقاط أساسية بس.
خليك مختصر ومباشر.

المحتوى:
{text}
""",
        "explanation": f"""إنت مساعد طالب جامعي في كلية الحاسبات والذكاء الاصطناعي.
المحتوى ده من محاضرة بالإنجليزي.

اعملي **شرح تفصيلي بالعربي** للمحتوى كله، بشرط:

1. اشرح **كل نقطة** بالتفصيل
2. ادي **أمثلة** على كل نقطة
3. اشرح **المصطلحات** جوا السياق
4. نظّم الشرح في **أجزاء صغيرة** (كل جزء 3-4 أسطر)

المحتوى:
{text}
""",
        "terms": f"""إنت مساعد طالب جامعي في كلية الحاسبات والذكاء الاصطناعي.
المحتوى ده من محاضرة بالإنجليزي.

اعملي **قائمة المصطلحات المهمة** بالشكل ده:

🔤 **المصطلح**
📖 المعنى بالعربي
💡 مثال

خليها 10-15 مصطلح أساسي.

المحتوى:
{text}
""",
        "quiz": f"""إنت مساعد طالب جامعي في كلية الحاسبات والذكاء الاصطناعي.
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
        "examples": f"""إنت مساعد طالب جامعي في كلية الحاسبات والذكاء الاصطناعي.
المحتوى ده من محاضرة بالإنجليزي.

اعملي **5 أمثلة عملية من الحياة الواقعية** على المفاهيم اللي في المحتوى.
كل مثال:
🎯 المفهوم
💡 المثال
📝 الشرح

المحتوى:
{text}
""",
        "problems": f"""إنت مساعد طالب جامعي في كلية الحاسبات والذكاء الاصطناعي.
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

    # شيل ### (عناوين)
    text = text.replace("###", "▪")
    text = text.replace("##", "◈")
    text = text.replace("#", "•")

    # شيل ** (bold)
    text = text.replace("**", "")

    # شيل --- (خطوط فاصلة)
    text = text.replace("---", "━━━━━━━━━━━━━")

    # شيل * في بداية الكلام
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
    get_or_create_user(user.id, user.username, user.first_name)

    plan = get_user_plan(user.id)
    allowed, remaining = check_limit(user.id)
    points, level = get_user_points(user.id)
    level_info = get_level_info(points)

    plan_names = {
        "free": "🆓 مجاني",
        "premium": "⭐ مميز",
        "admin": "👑 أدمن",
    }

    welcome = (
        f"أهلاً *{user.first_name}*! 👋\n\n"
        f"🎓 إنت في *ذاكر* - مساعدك الدراسي\n\n"
        f"💎 *نقاطك:* {points}\n"
        f"🏆 *مستواك:* {level_info['name']}\n"
        f"👤 *حسابك:* {plan_names.get(plan, 'مجاني')}\n"
        f"📊 *متبقي اليوم:* {remaining} استخدام\n\n"
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
        "/invite - دعوة أصدقاء"
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
    """أمر /points"""
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
    """أمر /daily"""
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
    """أمر /leaderboard"""
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
    """أمر /invite"""
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


# ===== معالجة الأزرار Inline =====
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة ضغطات الأزرار Inline"""
    query = update.callback_query
    await query.answer()

    data = query.data
    user = query.from_user

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
        await query.edit_message_text(
            "📸 *ارفع صورة*\n\n_قريب إن شاء الله_ 🚧"
        )
        return

    # أزرار الكويز
    if data == "quiz_from_pdf":
        await query.edit_message_text(
            "🎯 *كويز من PDF*\n\nارفع ملف PDF الأول."
        )
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

    # أزرار الشرح
    if data == "explain_concept":
        await query.edit_message_text("💡 *اشرحلي مفهوم*\n\nابعتلي اسم المفهوم.")
        return

    if data == "explain_term":
        await query.edit_message_text("🔤 *اشرحلي مصطلح*\n\nابعتلي المصطلح.")
        return

    if data == "solve_problem":
        await query.edit_message_text("🧮 *حل مسألة*\n\nابعتلي المسألة.")
        return

    # أزرار الترجمة
    if data == "translate_text":
        await query.edit_message_text("🌍 *ترجمة نص*\n\nابعتلي النص.")
        return

    if data == "translate_file":
        await query.edit_message_text("📄 *ترجمة ملف*\n\nارفع الملف.")
        return

    # أزرار التلخيص
    if data == "summarize_text":
        await query.edit_message_text("📝 *تلخيص نص*\n\nابعتلي النص.")
        return

    if data == "summarize_file":
        await query.edit_message_text("📄 *تلخيص ملف*\n\nارفع الملف.")
        return

    # أزرار الحساب
    if data == "account_info":
        plan = get_user_plan(user.id)
        allowed, remaining = check_limit(user.id)
        points, level = get_user_points(user.id)
        level_info = get_level_info(points)

        plan_names = {
            "free": "🆓 مجاني",
            "premium": "⭐ مميز",
            "admin": "👑 أدمن",
        }

        text = (
            f"👤 *بياناتك*\n\n"
            f"📛 الاسم: {user.first_name}\n"
            f"🆔 الـ ID: `{user.id}`\n"
            f"📊 الحساب: {plan_names.get(plan, 'مجاني')}\n"
            f"💎 النقاط: {points}\n"
            f"🏆 المستوى: {level_info['name']}\n"
            f"✅ متبقي اليوم: {remaining} استخدام\n"
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
            # ===== أزرار لوحة التحكم (Admin) =====
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
        
        text = "👥 *آخر 20 مستخدم:*\n\n"
        for user_id, first_name, username, points, level, plan, last_used in users:
            plan_emoji = {"free": "🆓", "premium": "⭐", "admin": "👑", "banned": "🚫"}.get(plan, "🆓")
            text += f"{plan_emoji} *{first_name or 'مستخدم'}* — {points} 💎\n"
            text += f"   🆔 `{user_id}`\n\n"
        
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=admin_panel_menu()
        )
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
    """لما المستخدم يختار نوع التحليل"""
    query = update.callback_query
    data = query.data

    # لو الكود مش analysis_، نروح للـ button_handler
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
        result = analyze_pdf_content(pdf_text, analysis_type)
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
    """لما المستخدم يبعت PDF"""
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
    """معالجة الأزرار اللي تحت الشات"""
    text = update.message.text
    user = update.effective_user

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