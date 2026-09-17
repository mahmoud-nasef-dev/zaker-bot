from telegram import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)


# ===== القائمة الرئيسية =====
def main_menu(is_admin=False):
    """القائمة الأساسية - بتفرق بين Admin والمستخدم العادي"""
    keyboard = [
        [KeyboardButton("📄 تحليل PDF"), KeyboardButton("📸 صورة")],
        [KeyboardButton("🎯 كويز"), KeyboardButton("📚 شرح")],
        [KeyboardButton("🌍 ترجمة"), KeyboardButton("📝 تلخيص")],
        [KeyboardButton("💎 نقاطي"), KeyboardButton("🎁 هدية يومية")],
        [KeyboardButton("🏆 المتصدرين"), KeyboardButton("👥 دعوة أصدقاء")],
        [KeyboardButton("📚 موادي"), KeyboardButton("🧠 حللني")],
        [KeyboardButton("📊 خطتي"), KeyboardButton("🏆 إنجازاتي")],
    ]

    if is_admin:
        keyboard.append([KeyboardButton("🎛️ لوحة التحكم")])

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        input_field_placeholder="اختار من الأزرار..."
    )


# ===== أزرار الرجوع =====
def back_button():
    """زرار الرجوع"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_home")]
    ])


# ===== أزرار إدخال المواد =====
def skip_subjects_button():
    """زر تخطي إدخال المواد"""
    keyboard = [
        [InlineKeyboardButton("📚 اكتبهم دلوقتي", callback_data="enter_subjects")],
        [InlineKeyboardButton("⏭️ تخطي دلوقتي", callback_data="skip_subjects")],
    ]
    return InlineKeyboardMarkup(keyboard)


def subjects_menu():
    """قائمة إدارة المواد"""
    keyboard = [
        [InlineKeyboardButton("➕ ضيف مادة", callback_data="add_subject")],
        [InlineKeyboardButton("📋 موادي", callback_data="list_subjects")],
        [InlineKeyboardButton("🗑️ احذف مادة", callback_data="delete_subject_menu")],
        [InlineKeyboardButton("🔄 مسح الكل", callback_data="clear_all_subjects")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_home")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ===== قوائم مختلفة =====
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
        [InlineKeyboardButton("📚 موادي", callback_data="my_subjects")],
        [InlineKeyboardButton("💎 ترقية الحساب", callback_data="account_upgrade")],
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


# ============================================
# ===== أزرار التحليل الشخصي (جديد) =====
# ============================================

def analysis_start_menu():
    """شاشة بداية التحليل"""
    keyboard = [
        [InlineKeyboardButton("🚀 يلا نبدأ", callback_data="analysis_begin")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="analysis_cancel")],
    ]
    return InlineKeyboardMarkup(keyboard)


def analysis_q1_time():
    """سؤال 1: وقت المذاكرة"""
    keyboard = [
        [InlineKeyboardButton("🌅 الصبح (6-12)", callback_data="ans_q1_morning")],
        [InlineKeyboardButton("☀️ العصر (12-5)", callback_data="ans_q1_afternoon")],
        [InlineKeyboardButton("🌙 بالليل (5-10)", callback_data="ans_q1_evening")],
        [InlineKeyboardButton("🦉 بعد منتصف الليل", callback_data="ans_q1_night")],
        [InlineKeyboardButton("⏭️ تخطي السؤال", callback_data="ans_skip")],
    ]
    return InlineKeyboardMarkup(keyboard)


def analysis_q2_duration():
    """سؤال 2: مدة التركيز"""
    keyboard = [
        [InlineKeyboardButton("⏰ 15 دقيقة", callback_data="ans_q2_15")],
        [InlineKeyboardButton("⏰ 25 دقيقة", callback_data="ans_q2_25")],
        [InlineKeyboardButton("⏰ 45 دقيقة", callback_data="ans_q2_45")],
        [InlineKeyboardButton("⏰ ساعة أو أكتر", callback_data="ans_q2_60")],
        [InlineKeyboardButton("⏭️ تخطي السؤال", callback_data="ans_skip")],
    ]
    return InlineKeyboardMarkup(keyboard)


def analysis_q3_style():
    """سؤال 3: نمط التعلم"""
    keyboard = [
        [InlineKeyboardButton("📊 بالرسومات", callback_data="ans_q3_visual")],
        [InlineKeyboardButton("🎬 بالفيديو", callback_data="ans_q3_video")],
        [InlineKeyboardButton("📖 بالقراءة", callback_data="ans_q3_reading")],
        [InlineKeyboardButton("💪 بالممارسة", callback_data="ans_q3_practice")],
        [InlineKeyboardButton("⏭️ تخطي السؤال", callback_data="ans_skip")],
    ]
    return InlineKeyboardMarkup(keyboard)


def analysis_q4_hard_subject(subjects):
    """سؤال 4: أصعب مادة - حسب المواد"""
    keyboard = []

    if subjects and len(subjects) > 0:
        # نستخدم مواد المستخدم
        for subject in subjects[:4]:
            keyboard.append([
                InlineKeyboardButton(f"📚 {subject}", callback_data=f"ans_q4_subj_{subject}")
            ])
    else:
        # مواد عامة
        keyboard = [
            [InlineKeyboardButton("🔤 عربي", callback_data="ans_q4_subj_عربي")],
            [InlineKeyboardButton("🌍 إنجليزي", callback_data="ans_q4_subj_إنجليزي")],
            [InlineKeyboardButton("🧮 رياضيات", callback_data="ans_q4_subj_رياضيات")],
            [InlineKeyboardButton("💻 برمجة", callback_data="ans_q4_subj_برمجة")],
        ]

    keyboard.append([InlineKeyboardButton("⏭️ تخطي السؤال", callback_data="ans_skip")])
    return InlineKeyboardMarkup(keyboard)


def analysis_q5_goal():
    """سؤال 5: الهدف"""
    keyboard = [
        [InlineKeyboardButton("📝 أنجح بس", callback_data="ans_q5_pass")],
        [InlineKeyboardButton("🏆 أتفوق", callback_data="ans_q5_excel")],
        [InlineKeyboardButton("💼 أشتغل", callback_data="ans_q5_work")],
        [InlineKeyboardButton("🎓 أكمل دراسات", callback_data="ans_q5_study")],
        [InlineKeyboardButton("⏭️ تخطي السؤال", callback_data="ans_skip")],
    ]
    return InlineKeyboardMarkup(keyboard)


def analysis_q6_exams():
    """سؤال 6: الامتحانات"""
    keyboard = [
        [InlineKeyboardButton("🔥 بعد أسبوع", callback_data="ans_q6_week")],
        [InlineKeyboardButton("📅 بعد شهر", callback_data="ans_q6_month")],
        [InlineKeyboardButton("🗓️ بعد شهرين أو أكتر", callback_data="ans_q6_2months")],
        [InlineKeyboardButton("⏳ مش عارف", callback_data="ans_q6_unknown")],
        [InlineKeyboardButton("⏭️ تخطي السؤال", callback_data="ans_skip")],
    ]
    return InlineKeyboardMarkup(keyboard)


def analysis_result_menu():
    """قائمة بعد التحليل"""
    keyboard = [
        [InlineKeyboardButton("📊 اعرض خطتي", callback_data="show_my_plan")],
        [InlineKeyboardButton("🔄 اعد التحليل", callback_data="analysis_restart")],
        [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="back_home")],
    ]
    return InlineKeyboardMarkup(keyboard)


def analysis_needed_menu():
    """قائمة تظهر لما المستخدم يحتاج تحليل الأول"""
    keyboard = [
        [InlineKeyboardButton("🧠 حللني دلوقتي", callback_data="analysis_begin")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_home")],
    ]
    return InlineKeyboardMarkup(keyboard)