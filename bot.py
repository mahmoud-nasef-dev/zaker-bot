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
    DEVELOPER_NAME, DEVELOPER_USERNAME, ADMIN_IDS
)
from database import (
    init_db, get_or_create_user, increment_usage,
    check_limit, get_user_plan, get_stats
)
from keyboards import (
    main_menu, pdf_menu, quiz_menu, explain_menu,
    translate_menu, summarize_menu, account_menu,
    admin_menu, back_button
)
from pdf_generator import create_pdf_report
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

1. اشرح **كل نقطة** بالتفصيل الممل
2. ادي **أمثلة** على كل نقطة
3. اشرح **المصطلحات** جوا السياق
4. نظّم الشرح في **أجزاء صغيرة** (كل جزء 3-4 أسطر)
5. اكتب بالعربي السهل المفهوم

المحتوى:
{text}
""",
        "terms": f"""إنت مساعد طالب جامعي في كلية الحاسبات والذكاء الاصطناعي.
المحتوى ده من محاضرة بالإنجليزي.

اعملي **قائمة المصطلحات المهمة** بالشكل ده:

🔤 **المصطلح** (النطق)
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
    response = model.generate_content(prompt)
    return response.text


# ===== لوحة التحكم (للأدمن) =====
def admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")],
        [InlineKeyboardButton("📢 بث رسالة", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_home")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ===== أزرار المستخدم =====
def main_keyboard():
    keyboard = [
        [InlineKeyboardButton("📄 ارفع PDF", callback_data="upload_pdf")],
        [InlineKeyboardButton("🌍 ترجمة", callback_data="translate"),
         InlineKeyboardButton("📚 تلخيص", callback_data="summarize")],
        [InlineKeyboardButton("ℹ️ عن البوت", callback_data="about")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ===== الأوامر =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = get_or_create_user(user.id, user.username, user.first_name)

    # جيب بيانات المستخدم
    from database import get_user_plan
    plan = get_user_plan(user.id)
    allowed, remaining = check_limit(user.id)

    plan_names = {
        "free": "🆓 مجاني",
        "premium": "⭐ مميز",
        "admin": "👑 أدمن",
    }

    welcome = (
        f"أهلاً *{user.first_name}*! 👋\n\n"
        f"🎓 إنت في *ذاكر* - مساعدك الدراسي\n\n"
        f"👤 حسابك: {plan_names.get(plan, 'مجاني')}\n"
        f"📊 متبقي اليوم: {remaining} استخدام\n\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"*اختار من الأزرار تحت* 👇"
    )

    # لو الأدمن، ضيف زرار لوحة التحكم
    if user.id in ADMIN_IDS:
        await update.message.reply_text(
            welcome,
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
    else:
        await update.message.reply_text(
            welcome,
            parse_mode="Markdown",
            reply_markup=main_menu()
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📚 *الأوامر المتاحة:*\n\n"
        "/start - البداية\n"
        "/help - مساعدة\n"
        "/about - عن البوت\n"
        "/myplan - خطتك الحالية\n\n"
        "أو ابعت أي نص مباشرة للترجمة والتلخيص."
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(ABOUT_MESSAGE, parse_mode="Markdown")


async def myplan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    plan = get_user_plan(user.id)

    plan_names = {
        "free": "🆓 مجاني",
        "premium": "⭐ مميز",
        "admin": "👑 أدمن",
    }

    allowed, remaining = check_limit(user.id)

    text = (
        f"👤 *حسابك:* {plan_names.get(plan, 'مجاني')}\n"
        f"📊 *متبقي اليوم:* {remaining} استخدام\n\n"
    )

    if plan == "free":
        text += f"💎 *للترقية:* تواصل مع {DEVELOPER_USERNAME}"

    await update.message.reply_text(text, parse_mode="Markdown")


# ===== معالجة الأزرار =====
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة ضغطات الأزرار Inline"""
    query = update.callback_query
    await query.answer()

    data = query.data
    user = query.from_user

    # ===== أزرار الرجوع =====
    if data == "back_home":
        await query.edit_message_text(
            "🏠 *القائمة الرئيسية*\n\nاختار من الأزرار تحت 👇",
            parse_mode="Markdown"
        )
        return

    # ===== أزرار PDF =====
    if data == "upload_pdf":
        await query.edit_message_text(
            "📄 *ارفع ملف PDF دلوقتي*\n\n"
            "ابعتلي الملف وأنا هحلله وهطلعلك:\n"
            "• ملخص بالعربي\n"
            "• مصطلحات مهمة\n"
            "• أسئلة للمراجعة\n\n"
            "_ملاحظة: الحد الأقصى 20 ميجا_",
            parse_mode="Markdown"
        )
        return

    if data == "upload_image":
        await query.edit_message_text(
            "📸 *ارفع صورة*\n\n"
            "ابعتلي صورة الكتاب أو السبورة وأنا هحللها.\n\n"
            "_الميزة دي قريب إن شاء الله_ 🚧"
        )
        return

    # ===== أزرار الكويز =====
    if data == "quiz_from_pdf":
        await query.edit_message_text(
            "🎯 *كويز من PDF*\n\n"
            "ارفع ملف PDF الأول، وبعدها هنعملك كويز عليه.\n\n"
            "_قريب إن شاء الله_ 🚧"
        )
        return

    if data == "quiz_random":
        await query.edit_message_text(
            "🎲 *كويز عشوائي*\n\n"
            "جاري التجهيز... 🚧"
        )
        return

    if data == "quiz_subject":
        await query.edit_message_text(
            "📚 *كويز من مادة*\n\n"
            "اختار المادة اللي عايز تختبر فيها.\n\n"
            "_قريب إن شاء الله_ 🚧"
        )
        return

    if data == "quiz_daily":
        await query.edit_message_text(
            "🎁 *الكويز اليومي*\n\n"
            "تعال كل يوم وخد سؤال جديد!\n\n"
            "_قريب إن شاء الله_ 🚧"
        )
        return

    # ===== أزرار الشرح =====
    if data == "explain_concept":
        await query.edit_message_text(
            "💡 *اشرحلي مفهوم*\n\n"
            "ابعتلي اسم المفهوم وهشرحلك إياه."
        )
        return

    if data == "explain_term":
        await query.edit_message_text(
            "🔤 *اشرحلي مصطلح*\n\n"
            "ابعتلي المصطلح وهشرحلك معناه."
        )
        return

    if data == "solve_problem":
        await query.edit_message_text(
            "🧮 *حل مسألة*\n\n"
            "ابعتلي المسألة وهحلها خطوة بخطوة."
        )
        return

    # ===== أزرار الترجمة =====
    if data == "translate_text":
        await query.edit_message_text(
            "🌍 *ترجمة نص*\n\n"
            "ابعتلي النص اللي عايز تترجمه."
        )
        return

    if data == "translate_file":
        await query.edit_message_text(
            "📄 *ترجمة ملف*\n\n"
            "ارفع الملف وهترجمهولك."
        )
        return

    # ===== أزرار التلخيص =====
    if data == "summarize_text":
        await query.edit_message_text(
            "📝 *تلخيص نص*\n\n"
            "ابعتلي النص اللي عايز تلخصه."
        )
        return

    if data == "summarize_file":
        await query.edit_message_text(
            "📄 *تلخيص ملف*\n\n"
            "ارفع الملف وهلخصهولك."
        )
        return

    # ===== أزرار الحساب =====
    if data == "account_info":
        plan = get_user_plan(user.id)
        allowed, remaining = check_limit(user.id)
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
            f"✅ متبقي اليوم: {remaining} استخدام\n"
        )

        await query.edit_message_text(text, parse_mode="Markdown")
        return

    if data == "account_stats":
        await query.edit_message_text(
            "📊 *إحصائياتك*\n\n"
            "_قريب إن شاء الله_ 🚧"
        )
        return

    if data == "account_badges":
        await query.edit_message_text(
            "🎖️ *إنجازاتك*\n\n"
            "_قريب إن شاء الله_ 🚧"
        )
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

    # ===== أزرار الأدمن =====
    if data == "admin_panel" and user.id in ADMIN_IDS:
        await query.edit_message_text(
            "🎛️ *لوحة التحكم*\n\nاختار من الأزرار:",
            parse_mode="Markdown",
            reply_markup=admin_menu()
        )
        return

    if data == "admin_stats" and user.id in ADMIN_IDS:
        stats = get_stats()
        text = (
            f"📊 *إحصائيات البوت*\n\n"
            f"👥 المستخدمين: {stats['total_users']}\n"
            f"⭐ المشتركين: {stats['premium_users']}\n"
            f"📨 إجمالي الطلبات: {stats['total_requests']}\n"
        )
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=admin_menu()
        )
        return

    if data == "admin_users" and user.id in ADMIN_IDS:
        await query.edit_message_text(
            "👥 *قائمة المستخدمين*\n\n_قريب إن شاء الله_ 🚧",
            parse_mode="Markdown",
            reply_markup=admin_menu()
        )
        return

    if data == "admin_broadcast" and user.id in ADMIN_IDS:
        await query.edit_message_text(
            "📢 *بث رسالة*\n\n_قريب إن شاء الله_ 🚧",
            parse_mode="Markdown",
            reply_markup=admin_menu()
        )
        return

    # ===== أزرار عامة =====
    if data == "about":
        await query.edit_message_text(ABOUT_MESSAGE, parse_mode="Markdown")
        return

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
    report_path = f"report_{user.id}.pdf"

    try:
        # نزل الملف
        file = await document.get_file()
        await file.download_to_drive(pdf_path)

        # اقرا المحتوى
        await waiting.edit_text("📖 جاري قراءة المحتوى...")
        pdf_text = process_pdf(pdf_path)

        if not pdf_text.strip():
            await waiting.edit_text("❌ الملف فاضي أو مش مقروء.")
            return

               # نحفظ النص في الذاكرة
        context.user_data["pdf_text"] = pdf_text

        # اعرض خيارات التحليل
        from keyboards import analysis_options_menu

        await waiting.edit_text(
            f"✅ *تم تحميل الملف بنجاح!*\n\n"
            f"📝 *حجم المحتوى:* {len(pdf_text)} حرف\n\n"
            f"🎯 *اختار إيه اللي عايزه:*",
            parse_mode="Markdown",
            reply_markup=analysis_options_menu()
        )

        # امسح الملف المؤقت
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

    except Exception as e:
        await waiting.edit_text(f"❌ حصل خطأ: {str(e)}")
        # نمسح الملفات لو موجودة
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        if os.path.exists(report_path):
            os.remove(report_path)

async def handle_pdf_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لما المستخدم يختار نوع التحليل"""
    query = update.callback_query
    await query.answer()

    data = query.data
    user = query.from_user

    if not data.startswith("analysis_"):
        return

    analysis_type = data.replace("analysis_", "")

    # نجيب النص من الذاكرة
    pdf_text = context.user_data.get("pdf_text")
    if not pdf_text:
        await query.edit_message_text("⚠️ الملف مش موجود. ارفعه تاني.")
        return

    # نحدد النوع بالعربي
    types = {
        "summary": "📝 الملخص",
        "explanation": "📚 الشرح التفصيلي",
        "terms": "🔤 المصطلحات",
        "quiz": "🎯 الكويز",
        "examples": "💡 الأمثلة",
        "problems": "🧮 المسائل",
    }
    type_name = types.get(analysis_type, "📝 التحليل")

    # رسالة الانتظار
    await query.edit_message_text(f"⏳ جاري إعداد {type_name}...")

    try:
        # نستدعي Gemini
        result = analyze_pdf_content(pdf_text, analysis_type)
        result = clean_text(result)

        # نقسم النص لو طويل
        full_text = f"{type_name}:\n\n{result}"

        if len(full_text) <= 4000:
            await query.edit_message_text(full_text)
        else:
            # نقسم لجزئين
            await query.edit_message_text(full_text[:4000])
            await update.effective_chat.send_message(full_text[4000:])

        # نضيف نقاط
        increment_usage(user.id)

    except Exception as e:
        await query.edit_message_text(f"❌ حصل خطأ: {str(e)}")

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

        increment_usage(user.id)
        await waiting.edit_text(result)

    except Exception as e:
        await waiting.edit_text(f"❌ حصل خطأ: {str(e)}")


# ===== تشغيل =====

async def handle_reply_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الأزرار اللي تحت الشات (Reply Keyboard)"""
    text = update.message.text
    user = update.effective_user

    # ===== تحليل PDF =====
    if text == "📄 تحليل PDF":
        await update.message.reply_text(
            "📄 *ارفع ملف PDF دلوقتي*\n\nابعتلي الملف وأنا هحلله.",
            parse_mode="Markdown",
            reply_markup=pdf_menu()
        )
        return

    # ===== صورة =====
    if text == "📸 صورة":
        await update.message.reply_text(
            "📸 *ارفع صورة*\n\nابعتلي صورة الكتاب أو السبورة.",
            parse_mode="Markdown",
            reply_markup=pdf_menu()
        )
        return

    # ===== كويز =====
    if text == "🎯 كويز":
        await update.message.reply_text(
            "🎯 *اختار نوع الكويز:*",
            parse_mode="Markdown",
            reply_markup=quiz_menu()
        )
        return

    # ===== شرح =====
    if text == "📚 شرح":
        await update.message.reply_text(
            "📚 *اختار نوع الشرح:*",
            parse_mode="Markdown",
            reply_markup=explain_menu()
        )
        return

    # ===== ترجمة =====
    if text == "🌍 ترجمة":
        await update.message.reply_text(
            "🌍 *اختار نوع الترجمة:*",
            parse_mode="Markdown",
            reply_markup=translate_menu()
        )
        return

    # ===== تلخيص =====
    if text == "📝 تلخيص":
        await update.message.reply_text(
            "📝 *اختار نوع التلخيص:*",
            parse_mode="Markdown",
            reply_markup=summarize_menu()
        )
        return

    # ===== حسابي =====
    if text == "🏆 حسابي":
        await update.message.reply_text(
            "🏆 *حسابك:*",
            parse_mode="Markdown",
            reply_markup=account_menu()
        )
        return

    # ===== هدية يومية =====
    if text == "🎁 هدية يومية":
        await update.message.reply_text(
            "🎁 *الهدية اليومية*\n\n_قريب إن شاء الله_ 🚧"
        )
        return

    # ===== أي حاجة تانية =====
    await handle_message(update, context)


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