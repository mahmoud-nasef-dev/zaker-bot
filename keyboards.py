from telegram import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)


# ===== القائمة الرئيسية (Reply Keyboard) =====
def main_menu(is_admin=False):
    """القائمة الأساسية - بتفرق بين Admin والمستخدم العادي"""
    keyboard = [
        [KeyboardButton("📄 تحليل PDF"), KeyboardButton("📸 صورة")],
        [KeyboardButton("🎯 كويز"), KeyboardButton("📚 شرح")],
        [KeyboardButton("🌍 ترجمة"), KeyboardButton("📝 تلخيص")],
        [KeyboardButton("💎 نقاطي"), KeyboardButton("🎁 هدية يومية")],
        [KeyboardButton("🏆 المتصدرين"), KeyboardButton("👥 دعوة أصدقاء")],
    ]

    # لو Admin، نضيف زر لوحة التحكم
    if is_admin:
        keyboard.append([KeyboardButton("🎛️ لوحة التحكم")])

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        input_field_placeholder="اختار من الأزرار..."
    )

# ===== أزرار Inline =====
def back_button():
    """زرار الرجوع"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_home")]
    ])


def pdf_menu():
    """قائمة تحليل PDF"""
    keyboard = [
        [InlineKeyboardButton("📄 ارفع ملف PDF", callback_data="upload_pdf")],
        [InlineKeyboardButton("📸 ارفع صورة", callback_data="upload_image")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_home")],
    ]
    return InlineKeyboardMarkup(keyboard)


def quiz_menu():
    """قائمة الكويز"""
    keyboard = [
        [InlineKeyboardButton("📄 كويز من PDF", callback_data="quiz_from_pdf")],
        [InlineKeyboardButton("🎲 كويز عشوائي", callback_data="quiz_random")],
        [InlineKeyboardButton("📚 كويز من مادة", callback_data="quiz_subject")],
        [InlineKeyboardButton("🎁 الكويز اليومي", callback_data="quiz_daily")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_home")],
    ]
    return InlineKeyboardMarkup(keyboard)


def explain_menu():
    """قائمة الشرح"""
    keyboard = [
        [InlineKeyboardButton("💡 اشرحلي مفهوم", callback_data="explain_concept")],
        [InlineKeyboardButton("🔤 اشرحلي مصطلح", callback_data="explain_term")],
        [InlineKeyboardButton("🧮 حل مسألة", callback_data="solve_problem")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_home")],
    ]
    return InlineKeyboardMarkup(keyboard)


def translate_menu():
    """قائمة الترجمة"""
    keyboard = [
        [InlineKeyboardButton("📝 نص للترجمة", callback_data="translate_text")],
        [InlineKeyboardButton("📄 ملف للترجمة", callback_data="translate_file")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_home")],
    ]
    return InlineKeyboardMarkup(keyboard)


def summarize_menu():
    """قائمة التلخيص"""
    keyboard = [
        [InlineKeyboardButton("📝 نص للتلخيص", callback_data="summarize_text")],
        [InlineKeyboardButton("📄 ملف للتلخيص", callback_data="summarize_file")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_home")],
    ]
    return InlineKeyboardMarkup(keyboard)


def account_menu():
    """قائمة الحساب"""
    keyboard = [
        [InlineKeyboardButton("👤 بياناتي", callback_data="account_info")],
        [InlineKeyboardButton("📊 إحصائياتي", callback_data="account_stats")],
        [InlineKeyboardButton("🎖️ إنجازاتي", callback_data="account_badges")],
        [InlineKeyboardButton("💎 ترقية الحساب", callback_data="account_upgrade")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_home")],
    ]
    return InlineKeyboardMarkup(keyboard)


def admin_menu():
    """قائمة الأدمن"""
    keyboard = [
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")],
        [InlineKeyboardButton("👥 المستخدمين", callback_data="admin_users")],
        [InlineKeyboardButton("📢 بث رسالة", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_home")],
    ]
    return InlineKeyboardMarkup(keyboard)
def analysis_options_menu():
    """قائمة خيارات التحليل بعد رفع PDF"""
    keyboard = [
        [InlineKeyboardButton("📝 ملخص سريع", callback_data="analysis_summary")],
        [InlineKeyboardButton("📚 شرح تفصيلي", callback_data="analysis_explanation")],
        [InlineKeyboardButton("🔤 مصطلحات", callback_data="analysis_terms")],
        [InlineKeyboardButton("🎯 كويز تفاعلي", callback_data="analysis_quiz")],
        [InlineKeyboardButton("💡 أمثلة عملية", callback_data="analysis_examples")],
        [InlineKeyboardButton("🧮 تمارين ومسائل", callback_data="analysis_problems")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_home")],
    ]
    return InlineKeyboardMarkup(keyboard)
def points_menu():
    """قائمة النقاط"""
    keyboard = [
        [InlineKeyboardButton("🎁 هدية يومية", callback_data="claim_daily")],
        [InlineKeyboardButton("🏆 المتصدرين", callback_data="show_leaderboard")],
        [InlineKeyboardButton("👥 دعوة صديق", callback_data="invite_friend")],
        [InlineKeyboardButton("📊 إحصائياتي", callback_data="my_stats")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_home")],
    ]
    return InlineKeyboardMarkup(keyboard)


def admin_menu():
    """قائمة الأدمن"""
    keyboard = [
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")],
        [InlineKeyboardButton("👥 المستخدمين", callback_data="admin_users")],
        [InlineKeyboardButton("📢 بث رسالة", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_home")],
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_panel_menu():
    """لوحة تحكم الأدمن"""
    keyboard = [
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")],
        [InlineKeyboardButton("👥 المستخدمين", callback_data="admin_users")],
        [InlineKeyboardButton("📢 بث رسالة", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_home")],
    ]
    return InlineKeyboardMarkup(keyboard)


def admin_user_actions(user_id):
    """أزرار التحكم في مستخدم معين"""
    keyboard = [
        [InlineKeyboardButton("⭐ ترقية لـ Premium", callback_data=f"admin_upgrade_{user_id}")],
        [InlineKeyboardButton("💎 إضافة نقاط", callback_data=f"admin_addpoints_{user_id}")],
        [InlineKeyboardButton("🚫 حظر", callback_data=f"admin_ban_{user_id}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="admin_users")],
    ]
    return InlineKeyboardMarkup(keyboard)