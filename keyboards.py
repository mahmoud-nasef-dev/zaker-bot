from telegram import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)


# ===== القائمة الرئيسية =====
def main_menu(is_admin=False):
    """القائمة الأساسية - بتفرق بين Admin والمستخدم العادي"""
    keyboard = [
        [KeyboardButton("📄 تحليل PDF"), KeyboardButton("🎯 كويز ذكي")],
        [KeyboardButton("📚 شرح"), KeyboardButton("🌍 ترجمة")],
        [KeyboardButton("📝 تلخيص"), KeyboardButton("💎 نقاطي")],
        [KeyboardButton("🎁 هدية يومية"), KeyboardButton("🏆 المتصدرين")],
        [KeyboardButton("👥 دعوة أصدقاء"), KeyboardButton("📚 موادي")],
        [KeyboardButton("🧠 حللني"), KeyboardButton("📊 خطتي")],
        [KeyboardButton("⏱️ ذاكر معايا"), KeyboardButton("🏆 إنجازاتي")],
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
    """قائمة الكويز (القديمة - للتوافق)"""
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
    """قائمة خيارات تحليل PDF (القديمة - للتحليل السريع)"""
    keyboard = [
        [InlineKeyboardButton("📝 ملخص سريع", callback_data="pdf_summary")],
        [InlineKeyboardButton("📚 شرح تفصيلي", callback_data="pdf_explanation")],
        [InlineKeyboardButton("🔤 مصطلحات", callback_data="pdf_terms")],
        [InlineKeyboardButton("🎯 كويز تفاعلي", callback_data="pdf_quiz")],
        [InlineKeyboardButton("💡 أمثلة عملية", callback_data="pdf_examples")],
        [InlineKeyboardButton("🧮 تمارين ومسائل", callback_data="pdf_problems")],
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
# ===== أزرار التحليل الشخصي =====
# ============================================

def analysis_start_menu():
    """شاشة بداية التحليل"""
    keyboard = [
        [InlineKeyboardButton("🚀 يلا نبدأ", callback_data="analysis_begin")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="analysis_cancel")],
    ]
    return InlineKeyboardMarkup(keyboard)


def analysis_q1_time():
    keyboard = [
        [InlineKeyboardButton("🌅 الصبح (6-12)", callback_data="ans_q1_morning")],
        [InlineKeyboardButton("☀️ العصر (12-5)", callback_data="ans_q1_afternoon")],
        [InlineKeyboardButton("🌙 بالليل (5-10)", callback_data="ans_q1_evening")],
        [InlineKeyboardButton("🦉 بعد منتصف الليل", callback_data="ans_q1_night")],
        [InlineKeyboardButton("⏭️ تخطي السؤال", callback_data="ans_skip")],
    ]
    return InlineKeyboardMarkup(keyboard)


def analysis_q2_duration():
    keyboard = [
        [InlineKeyboardButton("⏰ 15 دقيقة", callback_data="ans_q2_15")],
        [InlineKeyboardButton("⏰ 25 دقيقة", callback_data="ans_q2_25")],
        [InlineKeyboardButton("⏰ 45 دقيقة", callback_data="ans_q2_45")],
        [InlineKeyboardButton("⏰ ساعة أو أكتر", callback_data="ans_q2_60")],
        [InlineKeyboardButton("⏭️ تخطي السؤال", callback_data="ans_skip")],
    ]
    return InlineKeyboardMarkup(keyboard)


def analysis_q3_style():
    keyboard = [
        [InlineKeyboardButton("📊 بالرسومات", callback_data="ans_q3_visual")],
        [InlineKeyboardButton("🎬 بالفيديو", callback_data="ans_q3_video")],
        [InlineKeyboardButton("📖 بالقراءة", callback_data="ans_q3_reading")],
        [InlineKeyboardButton("💪 بالممارسة", callback_data="ans_q3_practice")],
        [InlineKeyboardButton("⏭️ تخطي السؤال", callback_data="ans_skip")],
    ]
    return InlineKeyboardMarkup(keyboard)


def analysis_q4_hard_subject(subjects):
    keyboard = []

    if subjects and len(subjects) > 0:
        for subject in subjects[:4]:
            keyboard.append([
                InlineKeyboardButton(f"📚 {subject}", callback_data=f"ans_q4_subj_{subject}")
            ])
    else:
        keyboard = [
            [InlineKeyboardButton("🔤 عربي", callback_data="ans_q4_subj_عربي")],
            [InlineKeyboardButton("🌍 إنجليزي", callback_data="ans_q4_subj_إنجليزي")],
            [InlineKeyboardButton("🧮 رياضيات", callback_data="ans_q4_subj_رياضيات")],
            [InlineKeyboardButton("💻 برمجة", callback_data="ans_q4_subj_برمجة")],
        ]

    keyboard.append([InlineKeyboardButton("⏭️ تخطي السؤال", callback_data="ans_skip")])
    return InlineKeyboardMarkup(keyboard)


def analysis_q5_goal():
    keyboard = [
        [InlineKeyboardButton("📝 أنجح بس", callback_data="ans_q5_pass")],
        [InlineKeyboardButton("🏆 أتفوق", callback_data="ans_q5_excel")],
        [InlineKeyboardButton("💼 أشتغل", callback_data="ans_q5_work")],
        [InlineKeyboardButton("🎓 أكمل دراسات", callback_data="ans_q5_study")],
        [InlineKeyboardButton("⏭️ تخطي السؤال", callback_data="ans_skip")],
    ]
    return InlineKeyboardMarkup(keyboard)


def analysis_q6_exams():
    keyboard = [
        [InlineKeyboardButton("🔥 بعد أسبوع", callback_data="ans_q6_week")],
        [InlineKeyboardButton("📅 بعد شهر", callback_data="ans_q6_month")],
        [InlineKeyboardButton("🗓️ بعد شهرين أو أكتر", callback_data="ans_q6_2months")],
        [InlineKeyboardButton("⏳ مش عارف", callback_data="ans_q6_unknown")],
        [InlineKeyboardButton("⏭️ تخطي السؤال", callback_data="ans_skip")],
    ]
    return InlineKeyboardMarkup(keyboard)


def analysis_result_menu():
    keyboard = [
        [InlineKeyboardButton("📊 اعرض خطتي", callback_data="show_my_plan")],
        [InlineKeyboardButton("🔄 اعد التحليل", callback_data="analysis_restart")],
        [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="back_home")],
    ]
    return InlineKeyboardMarkup(keyboard)


def analysis_needed_menu():
    keyboard = [
        [InlineKeyboardButton("🧠 حللني دلوقتي", callback_data="analysis_begin")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_home")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ============================================
# ===== أزرار خطة المذاكرة =====
# ============================================

def plan_menu():
    """قائمة الخطة"""
    keyboard = [
        [InlineKeyboardButton("📅 خطتي الأسبوعية", callback_data="show_weekly_plan")],
        [InlineKeyboardButton("📚 خطة النهاردة", callback_data="show_today_plan")],
        [InlineKeyboardButton("⏱️ ابدأ جلسة", callback_data="start_pomodoro")],
        [InlineKeyboardButton("🔄 جدد الخطة", callback_data="regenerate_plan")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_home")],
    ]
    return InlineKeyboardMarkup(keyboard)


def plan_needs_analysis_menu():
    """لما المستخدم يطلب خطة بس مفيش تحليل"""
    keyboard = [
        [InlineKeyboardButton("🧠 حللني دلوقتي", callback_data="analysis_begin")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_home")],
    ]
    return InlineKeyboardMarkup(keyboard)


def pomodoro_start_menu():
    """بداية Pomodoro"""
    keyboard = [
        [InlineKeyboardButton("🚀 ابدأ الجلسة", callback_data="pomodoro_begin")],
        [InlineKeyboardButton("📚 اختار مادة", callback_data="pomodoro_choose_subject")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_home")],
    ]
    return InlineKeyboardMarkup(keyboard)


def pomodoro_duration_menu():
    """اختيار مدة الجلسة"""
    keyboard = [
        [InlineKeyboardButton("⏱️ 15 دقيقة", callback_data="pomodoro_15")],
        [InlineKeyboardButton("⏱️ 25 دقيقة", callback_data="pomodoro_25")],
        [InlineKeyboardButton("⏱️ 45 دقيقة", callback_data="pomodoro_45")],
        [InlineKeyboardButton("⏱️ 60 دقيقة", callback_data="pomodoro_60")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_home")],
    ]
    return InlineKeyboardMarkup(keyboard)


def pomodoro_subjects_menu(subjects):
    """اختيار المادة للجلسة"""
    keyboard = []

    if subjects and len(subjects) > 0:
        for subject in subjects[:5]:
            keyboard.append([
                InlineKeyboardButton(f"📚 {subject}", callback_data=f"pomodoro_subj_{subject}")
            ])
    else:
        keyboard.append([
            InlineKeyboardButton("⚠️ مفيش مواد، ضيف موادك", callback_data="my_subjects")
        ])

    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back_home")])
    return InlineKeyboardMarkup(keyboard)


def pomodoro_active_menu():
    """أثناء الجلسة"""
    keyboard = [
        [InlineKeyboardButton("✅ خلصت الجلسة", callback_data="pomodoro_done")],
        [InlineKeyboardButton("⏸️ إيقاف مؤقت", callback_data="pomodoro_pause")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="pomodoro_cancel")],
    ]
    return InlineKeyboardMarkup(keyboard)


def pomodoro_done_menu():
    """بعد الجلسة"""
    keyboard = [
        [InlineKeyboardButton("▶️ جلسة تانية", callback_data="pomodoro_again")],
        [InlineKeyboardButton("☕ راحة", callback_data="pomodoro_break")],
        [InlineKeyboardButton("🏠 خلصت النهاردة", callback_data="back_home")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ============================================
# ===== أزرار v1.1 - Pagination =====
# ============================================

def quick_actions_menu():
    """قائمة الـ Quick Actions بعد رفع PDF"""
    keyboard = [
        [InlineKeyboardButton("⚡ ملخص سريع (10 ثواني)", callback_data="quick_summary")],
        [InlineKeyboardButton("📚 شرح تفصيلي (فصول)", callback_data="full_explanation")],
        [InlineKeyboardButton("🔤 مصطلحات", callback_data="quick_terms")],
        [InlineKeyboardButton("🎯 كويز", callback_data="quick_quiz")],
        [InlineKeyboardButton("💬 اسألني عن الملف", callback_data="ask_pdf")],
        [InlineKeyboardButton("📥 حمّل التحليل", callback_data="download_analysis")],
    ]
    return InlineKeyboardMarkup(keyboard)


def chapters_menu(chapters):
    """قائمة الفصول"""
    keyboard = []

    for i, chapter in enumerate(chapters):
        title = chapter.get("title", f"الفصل {i+1}")
        parts_count = len(chapter.get("parts", []))
        keyboard.append([
            InlineKeyboardButton(
                f"📖 {title} ({parts_count} أجزاء)",
                callback_data=f"chapter_{i}"
            )
        ])

    keyboard.append([InlineKeyboardButton("📥 حمّل كل الشرح", callback_data="download_full_explanation")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back_home")])

    return InlineKeyboardMarkup(keyboard)


def chapter_nav_menu(chapter_idx, part_idx, total_parts):
    """أزرار التنقل بين الأجزاء"""
    keyboard = []
    nav_row = []

    if part_idx > 0:
        nav_row.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"prev_part_{chapter_idx}"))

    if part_idx < total_parts - 1:
        nav_row.append(InlineKeyboardButton("➡️ التالي", callback_data=f"next_part_{chapter_idx}"))

    if nav_row:
        keyboard.append(nav_row)

    keyboard.append([
        InlineKeyboardButton("📋 فهرس الفصول", callback_data="show_chapters")
    ])
    keyboard.append([
        InlineKeyboardButton("📥 حمّل كل الشرح", callback_data="download_full_explanation")
    ])
    keyboard.append([InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="back_home")])

    return InlineKeyboardMarkup(keyboard)


def chapter_options_menu():
    """قائمة بعد عرض فصل"""
    keyboard = [
        [InlineKeyboardButton("💡 اشرح الفصل كامل", callback_data="explain_full_chapter")],
        [InlineKeyboardButton("📌 اشرح جزء جزء", callback_data="explain_part_by_part")],
        [InlineKeyboardButton("🎯 امتحنّي على الفصل", callback_data="quiz_this_chapter")],
        [InlineKeyboardButton("📋 فهرس الفصول", callback_data="show_chapters")],
        [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="back_home")],
    ]
    return InlineKeyboardMarkup(keyboard)


def back_to_chapters_menu():
    """رجوع للفصول"""
    keyboard = [
        [InlineKeyboardButton("📋 فهرس الفصول", callback_data="show_chapters")],
        [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="back_home")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ============================================
# ===== أزرار V2 - Quiz Engine (جديد) =====
# ============================================

def smart_quiz_menu():
    """قائمة الكويز الذكي (V2)"""
    keyboard = [
        [InlineKeyboardButton("📚 كويز على المحاضرة", callback_data="smart_quiz_lecture")],
        [InlineKeyboardButton("🎯 كويز على نقاط ضعفي", callback_data="smart_quiz_weak")],
        [InlineKeyboardButton("❌ مراجعة أخطائي", callback_data="smart_quiz_mistakes")],
        [InlineKeyboardButton("🎲 الكويز اليومي", callback_data="smart_quiz_daily")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_home")],
    ]
    return InlineKeyboardMarkup(keyboard)


def quiz_count_menu(mode):
    """اختيار عدد الأسئلة (V2)"""
    keyboard = [
        [InlineKeyboardButton("5 أسئلة (سريع)", callback_data=f"quiz_count_5_{mode}")],
        [InlineKeyboardButton("10 أسئلة (متوسط)", callback_data=f"quiz_count_10_{mode}")],
        [InlineKeyboardButton("15 أسئلة (كامل)", callback_data=f"quiz_count_15_{mode}")],
        [InlineKeyboardButton("20 أسئلة (مكثف)", callback_data=f"quiz_count_20_{mode}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="smart_quiz_back")],
    ]
    return InlineKeyboardMarkup(keyboard)


def quiz_difficulty_menu(count, mode):
    """اختيار صعوبة الأسئلة (V2)"""
    keyboard = [
        [InlineKeyboardButton("🟢 سهل", callback_data=f"quiz_diff_easy_{count}_{mode}")],
        [InlineKeyboardButton("🟡 متوسط", callback_data=f"quiz_diff_medium_{count}_{mode}")],
        [InlineKeyboardButton("🔴 صعب", callback_data=f"quiz_diff_hard_{count}_{mode}")],
        [InlineKeyboardButton("🧠 تكيفي (موصى به)", callback_data=f"quiz_diff_adaptive_{count}_{mode}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="smart_quiz_back")],
    ]
    return InlineKeyboardMarkup(keyboard)


def quiz_question_menu(question_num, total):
    """أزرار الإجابة على السؤال (A/B/C/D) (V2)"""
    keyboard = [
        [InlineKeyboardButton("A", callback_data="quiz_ans_A")],
        [InlineKeyboardButton("B", callback_data="quiz_ans_B")],
        [InlineKeyboardButton("C", callback_data="quiz_ans_C")],
        [InlineKeyboardButton("D", callback_data="quiz_ans_D")],
        [InlineKeyboardButton("⏭️ تخطي السؤال", callback_data="quiz_skip")],
        [InlineKeyboardButton("🛑 إنهاء الكويز", callback_data="quiz_finish")],
    ]
    return InlineKeyboardMarkup(keyboard)


def quiz_after_answer_menu(is_correct, has_misconception=False):
    """أزرار بعد الإجابة (V2)"""
    keyboard = []

    if not is_correct and has_misconception:
        keyboard.append([
            InlineKeyboardButton("💡 فهمني غلطتي", callback_data="quiz_explain_mistake")
        ])

    keyboard.append([
        InlineKeyboardButton("➡️ السؤال التالي", callback_data="quiz_next_question")
    ])
    keyboard.append([
        InlineKeyboardButton("🛑 إنهاء الكويز", callback_data="quiz_finish")
    ])

    return InlineKeyboardMarkup(keyboard)


def quiz_result_menu():
    """قائمة بعد انتهاء الكويز (V2)"""
    keyboard = [
        [InlineKeyboardButton("🔄 كويز تاني", callback_data="smart_quiz_restart")],
        [InlineKeyboardButton("📚 اشرحلي نقاط ضعفي", callback_data="quiz_explain_weak")],
        [InlineKeyboardButton("🎯 كويز على نقاط ضعفي", callback_data="smart_quiz_weak")],
        [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="back_home")],
    ]
    return InlineKeyboardMarkup(keyboard)


def quiz_mistake_explanation_menu(question_num):
    """أزرار شرح الغلطة (V2)"""
    keyboard = [
        [InlineKeyboardButton("➡️ السؤال التالي", callback_data="quiz_next_question")],
        [InlineKeyboardButton("🛑 إنهاء الكويز", callback_data="quiz_finish")],
    ]
    return InlineKeyboardMarkup(keyboard)


def quiz_no_source_menu():
    """لما المستخدم يبدأ كويز ومفيش مصدر"""
    keyboard = [
        [InlineKeyboardButton("📄 ارفع ملف PDF الأول", callback_data="upload_pdf")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_home")],
    ]
    return InlineKeyboardMarkup(keyboard)


def quiz_processing_menu():
    """أثناء تجهيز بنك الأسئلة (V2)"""
    keyboard = [
        [InlineKeyboardButton("🛑 إلغاء", callback_data="quiz_cancel")],
    ]
    return InlineKeyboardMarkup(keyboard)