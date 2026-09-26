# ============================================
#   إعدادات البوت - ذاكر
#   Version: 2.0.0-dev (V2 - Quiz Engine)
# ============================================

# ===== معلومات المطور =====
DEVELOPER_NAME = "Mahmoud Nasef"
DEVELOPER_USERNAME = "@salafimahmoudnasef"
DEVELOPER_ID = 8910760285

# ===== معلومات البوت =====
BOT_NAME = "ذاكر"
BOT_USERNAME = "@trans_service_egypt_bot"
BOT_VERSION = "2.0.0-dev"

# ===== صلاحيات الأدمن =====
ADMIN_IDS = [
    DEVELOPER_ID,
]

# ===== الحدود =====
FREE_DAILY_LIMIT = 3
PREMIUM_DAILY_LIMIT = 100
ADMIN_DAILY_LIMIT = 99999

# ===== قاعدة البيانات =====
# ⚠️ V2 بيستخدم ملف منفصل عشان ميتعارضش مع V1
DATABASE_FILE = "users_v2.db"

# ===== إعدادات PDF =====
PDF_MAX_SIZE_MB = 20
PDF_MAX_CHARS = 100000
PDF_CHUNK_SIZE = 6000
PDF_MAX_CHUNKS = 8
PDF_QUICK_SUMMARY_CHARS = 15000

# ===== إعدادات AI (Groq للتحليل) =====
GROQ_MODEL = "openai/gpt-oss-20b"
AI_MAX_TOKENS = 4000
AI_TEMPERATURE = 0.7

# ===== إعدادات Mistral OCR =====
MISTRAL_OCR_MODEL = "mistral-ocr-latest"
MISTRAL_OCR_MAX_PAGES = 50
MISTRAL_OCR_TIMEOUT = 180

# ===== إعدادات الـ Pagination =====
CHAPTERS_MIN = 3
CHAPTERS_MAX = 5
PARTS_PER_CHAPTER_MIN = 2
PARTS_PER_CHAPTER_MAX = 5

# ===== إعدادات Quiz Engine (V2 - جديد) =====
# عدد المفاهيم الأقصى اللي يتم استخراجها من المحاضرة
QUIZ_MAX_CONCEPTS = 10

# عدد الأسئلة اللي يتم توليدها لكل مفهوم
QUIZ_QUESTIONS_PER_CONCEPT = 3

# عدد الأسئلة الافتراضي في الجلسة
QUIZ_DEFAULT_COUNT = 10

# حد أقصى للأسئلة في الجلسة
QUIZ_MAX_COUNT = 20

# Validation thresholds
QUIZ_MIN_QUESTION_LENGTH = 10
QUIZ_MAX_QUESTION_LENGTH = 500
QUIZ_MIN_OPTIONS = 2
QUIZ_MAX_OPTIONS = 6
QUIZ_MIN_EXPLANATION_LENGTH = 10

# Review intervals (بالأيام) - للـ Spaced Repetition
QUIZ_REVIEW_INTERVALS = [1, 3, 7, 14, 30]

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
🎯 كويز ذكي (جديد!)
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

# ===== رسائل Quiz Engine (V2 - جديد) =====
QUIZ_NO_SOURCE_ERROR = """
⚠️ *مفيش محاضرة محفوظة*

ارفع PDF الأول عشان نقدر نعمل كويز عليه.
"""

QUIZ_GENERATING_MESSAGE = """
🔄 *جاري تجهيز بنك الأسئلة...*

_دي أول مرة نعمل كويز على المحاضرة دي، ممكن ياخد دقيقة._
"""

QUIZ_NO_QUESTIONS_ERROR = """
❌ *مفيش أسئلة متاحة للمحاضرة دي*

جرب ترفع PDF تاني، أو استنى شوية.
"""

QUIZ_VALIDATION_ERROR = """
⚠️ *مقدرناش نجهز أسئلة كويسة من المحتوى ده*

جرب ترفع محاضرة تانية بمحتوى أوضح.
"""