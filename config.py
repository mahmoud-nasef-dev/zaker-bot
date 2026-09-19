# ============================================
#   إعدادات البوت - ذاكر
#   Version: 1.4.0 (Groq Vision)
# ============================================

# ===== معلومات المطور =====
DEVELOPER_NAME = "Mahmoud Nasef"
DEVELOPER_USERNAME = "@salafimahmoudnasef"
DEVELOPER_ID = 8910760285

# ===== معلومات البوت =====
BOT_NAME = "ذاكر"
BOT_USERNAME = "@trans_service_egypt_bot"
BOT_VERSION = "1.4.0"

# ===== صلاحيات الأدمن =====
ADMIN_IDS = [
    DEVELOPER_ID,
]

# ===== الحدود =====
FREE_DAILY_LIMIT = 3
PREMIUM_DAILY_LIMIT = 100
ADMIN_DAILY_LIMIT = 99999

# ===== قاعدة البيانات =====
DATABASE_FILE = "users.db"

# ===== إعدادات PDF =====
PDF_MAX_SIZE_MB = 20
PDF_MAX_CHARS = 100000
PDF_CHUNK_SIZE = 6000
PDF_MAX_CHUNKS = 8
PDF_QUICK_SUMMARY_CHARS = 15000

# ===== إعدادات AI (Groq فقط) =====
GROQ_MODEL = "openai/gpt-oss-20b"
GROQ_VISION_MODEL = "llama-3.2-90b-vision-preview"
AI_MAX_TOKENS = 4000
AI_TEMPERATURE = 0.7

# ===== إعدادات OCR =====
OCR_MAX_PAGES = 10           # أقصى عدد صفحات نحولها لصور (للأداء)
OCR_IMAGE_DPI = 150          # دقة الصورة (أعلى = أوضح بس أبطأ)
OCR_MAX_IMAGE_SIZE = 2000    # أقصى بُعد للصورة بالبكسل

# ===== إعدادات الـ Pagination =====
CHAPTERS_MIN = 3
CHAPTERS_MAX = 5
PARTS_PER_CHAPTER_MIN = 2
PARTS_PER_CHAPTER_MAX = 5

# ===== رسائل =====
WELCOME_MESSAGE = f"""
🚀 *أهلاً بيك في {BOT_NAME}*

أنا مساعدك الدراسي الذكي.
اقدر أساعدك في:

📄 *تحليل ملفات PDF* (بالعربي)
🧠 *تحليل شخصيتك الدراسية*
📊 *خطة مذاكرة مخصصة*
⏱️ *جلسات مذاكرة Pomodoro*
🌍 *ترجمة وتلخيص*
🎯 *كويز تفاعلي*

━━━━━━━━━━━━━━━━
👨‍💻 *تطوير:*
{DEVELOPER_NAME}

📱 *تواصل:*
{DEVELOPER_USERNAME}
━━━━━━━━━━━━━━━━

*جرب دلوقتي! ابدأ من الأزرار تحت* 👇
"""

ABOUT_MESSAGE = f"""
🤖 *{BOT_NAME}* v{BOT_VERSION}

📝 *الوصف:*
مساعد دراسي ذكي للطلاب الجامعيين.
كل حاجة بالعربي — حتى لو المحتوى إنجليزي!

━━━━━━━━━━━━━━━━
✨ *الميزات:*

📄 تحليل PDF (بالعربي)
🧠 تحليل شخصي
📊 خطة مذاكرة
⏱️ Pomodoro
🎯 كويزات
🌍 ترجمة
📝 تلخيص
💎 نظام نقاط ومستويات
🏆 لوحة متصدرين
👥 دعوة أصدقاء
━━━━━━━━━━━━━━━━

👨‍💻 *المطور:*
{DEVELOPER_NAME}

📱 *للتواصل:*
{DEVELOPER_USERNAME}

━━━━━━━━━━━━━━━━
🇪🇬 *صُنع في مصر*
"""

# ===== رسائل الخطأ =====
PDF_EMPTY_ERROR = """
❌ *الملف فاضي أو مش مقروء.*

💡 *الأسباب المحتملة:*
• الملف تالف أو غير مدعوم
• الملف محمي بكلمة سر
• مشكلة مؤقتة في الاتصال بالـ AI

🔁 *جرب:*
• ارفع الملف تاني
• تأكد إن الملف PDF أصلي
• لو استمرت المشكلة كلم المطور
"""

PDF_TOO_LARGE_ERROR = f"""
⚠️ *الملف كبير جداً!*

الحد الأقصى: {PDF_MAX_SIZE_MB} ميجا

🔁 *جرب:*
• اضغط الملف
• قسمه لأجزاء أصغر
• ارفع جزء جزء
"""

PDF_PROCESSING_ERROR = """
❌ *حصل خطأ أثناء معالجة الملف.*

🔁 جرب تاني، ولو استمرت المشكلة كلم المطور.
"""