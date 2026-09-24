# ============================================
#   Quiz Generator — V2
#   المسؤول عن: تحليل المحتوى + توليد الأسئلة
# ============================================

import os
import json
import re
from datetime import datetime

from groq import Groq
from dotenv import load_dotenv

from config import GROQ_MODEL, AI_MAX_TOKENS, AI_TEMPERATURE
from database import (
    save_concept, get_concepts_by_source,
    save_concept_relationship,
    save_question, count_questions_by_source,
)

# ===== الإعدادات =====
load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ============================================
#   دالة AI موحدة (Groq فقط)
# ============================================

def ai_generate(prompt, max_tokens=AI_MAX_TOKENS, json_mode=False):
    """بتوليد نص بـ Groq"""
    if len(prompt) > 25000:
        prompt = prompt[:25000] + "..."

    try:
        kwargs = {
            "model": GROQ_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "إنت مساعد تعليمي مصري. كل ردودك بالعربي. لما يُطلب منك JSON، رد بـ JSON فقط بدون أي كلام إضافي."
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": AI_TEMPERATURE,
            "max_tokens": max_tokens,
        }

        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = groq_client.chat.completions.create(**kwargs)
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Groq فشل: {e}")
        return None


# ============================================
#   دالة تنظيف JSON
# ============================================

def extract_json(text):
    """بتستخرج JSON من نص"""
    if not text:
        return None

    text = text.strip()
    text = text.replace("```json", "").replace("```", "").strip()

    start = text.find("{")
    end = text.rfind("}") + 1

    if start < 0 or end <= start:
        return None

    try:
        return json.loads(text[start:end])
    except Exception as e:
        print(f"⚠️ فشل قراءة JSON: {e}")
        return None


# ============================================
#   1. analyze_content — استخراج المفاهيم
# ============================================

def analyze_content(pdf_text, source_id, max_concepts=15):
    """بتحلل المحتوى وتستخرج المفاهيم الأساسية"""

    if not pdf_text or len(pdf_text.strip()) < 100:
        print("❌ النص قصير جداً")
        return []

    if len(pdf_text) > 20000:
        pdf_text = pdf_text[:20000] + "..."

    prompt = f"""إنت محلل تعليمي. حلل المحتوى ده واستخرج المفاهيم الأساسية.

📄 المحتوى:
{pdf_text}

━━━━━━━━━━━━━━━

🎯 المطلوب:
- استخرج أهم {max_concepts} مفهوم أساسي
- كل مفهوم له:
  - name: اسم المفهوم (بالإنجليزي لو أصله إنجليزي)
  - description: وصف مختصر (سطرين بالعربي)
  - importance: أهمية المفهوم (0.0 - 1.0)
  - difficulty: صعوبة المفهوم (0.0 - 1.0)
  - subconcepts: قائمة بالمفاهيم الفرعية (2-4 بس)

⚠️ مهم:
- رتب المفاهيم حسب الأهمية (الأهم أول)
- متكررش المفاهيم
- المفاهيم تكون من المحتوى نفسه، مش من بره

⚠️ رد بـ JSON فقط:

{{
  "concepts": [
    {{
      "name": "Recursion",
      "description": "...",
      "importance": 0.95,
      "difficulty": 0.75,
      "subconcepts": ["Base Case", "Recursive Case"]
    }}
  ]
}}"""

    print(f"🔍 جاري تحليل المحتوى (استخراج المفاهيم)...")
    response = ai_generate(prompt, max_tokens=3000, json_mode=True)

    if not response:
        print("❌ فشل استخراج المفاهيم")
        return []

    data = extract_json(response)
    if not data or "concepts" not in data:
        print("❌ فشل قراءة JSON")
        return []

    concepts = data["concepts"]

    if not isinstance(concepts, list):
        print("❌ الـ concepts مش list")
        return []

    concepts = [c for c in concepts if isinstance(c, dict)]

    print(f"✅ تم استخراج {len(concepts)} مفهوم")
    return concepts


# ============================================
#   دالة مساعدة: حفظ المفاهيم في Database
# ============================================

def save_concepts_to_db(source_id, concepts):
    """بتحفظ المفاهيم في Database"""
    concept_map = {}

    for concept in concepts:
        if not isinstance(concept, dict):
            continue

        name = concept.get("name", "").strip()
        if not name:
            continue

        description = concept.get("description", "")
        importance = float(concept.get("importance", 0.5))
        difficulty = float(concept.get("difficulty", 0.5))

        concept_id = save_concept(
            source_id=source_id,
            name=name,
            description=description,
            importance=importance,
            difficulty=difficulty,
        )

        if concept_id:
            concept_map[name] = concept_id
            print(f"  ✅ {name} (ID: {concept_id})")

    print(f"✅ تم حفظ {len(concept_map)} مفهوم في Database")
    return concept_map


# ============================================
#   2. build_concept_graph — بناء العلاقات
# ============================================

def build_concept_graph(concepts, pdf_text, source_id, concept_map):
    """بتبني العلاقات بين المفاهيم (Concept Graph)"""

    if not concepts or len(concepts) < 2:
        print("⚠️ مفيش مفاهيم كفاية لبناء علاقات")
        return 0

    concepts_list = []
    for c in concepts:
        if not isinstance(c, dict):
            continue
        name = c.get("name", "").strip()
        desc = c.get("description", "")
        if name:
            concepts_list.append(f"- {name}: {desc}")

    concepts_text = "\n".join(concepts_list)

    if len(pdf_text) > 10000:
        pdf_text = pdf_text[:10000] + "..."

    prompt = f"""إنت محلل تعليمي. حدد العلاقات بين المفاهيم دي.

📄 المحتوى:
{pdf_text}

━━━━━━━━━━━━━━━

📚 المفاهيم:
{concepts_text}

━━━━━━━━━━━━━━━

🎯 المطلوب:
حدد العلاقات بين المفاهيم. كل علاقة لها:
- from: المفهوم الأول (بالاسم)
- to: المفهوم التاني (بالاسم)
- type: نوع العلاقة
  * "prerequisite" = from لازم يتفهم قبل to
  * "related" = from و to مترابطين
  * "part_of" = from جزء من to
- confidence: مدى ثقتك (0.0 - 1.0)

⚠️ مهم:
- العلاقات تكون منطقية وواضحة من المحتوى
- متعملش علاقات كتير (5-15 علاقة)
- متعملش علاقات عكسية مكررة

⚠️ رد بـ JSON فقط:

{{
  "relationships": [
    {{
      "from": "Base Case",
      "to": "Recursion",
      "type": "prerequisite",
      "confidence": 0.95
    }}
  ]
}}"""

    print(f"🔗 جاري بناء العلاقات بين المفاهيم...")
    response = ai_generate(prompt, max_tokens=2500, json_mode=True)

    if not response:
        print("⚠️ فشل بناء العلاقات")
        return 0

    data = extract_json(response)
    if not data or "relationships" not in data:
        print("⚠️ فشل قراءة JSON")
        return 0

    relationships = data["relationships"]

    if not isinstance(relationships, list):
        print("⚠️ الـ relationships مش list")
        return 0

    saved_count = 0

    for rel in relationships:
        if not isinstance(rel, dict):
            continue

        from_name = rel.get("from", "").strip()
        to_name = rel.get("to", "").strip()
        rel_type = rel.get("type", "related")
        confidence = float(rel.get("confidence", 0.5))

        if from_name not in concept_map or to_name not in concept_map:
            continue

        from_id = concept_map[from_name]
        to_id = concept_map[to_name]

        success = save_concept_relationship(
            source_id=source_id,
            from_concept_id=from_id,
            to_concept_id=to_id,
            relationship_type=rel_type,
            confidence=confidence,
        )

        if success:
            saved_count += 1

    print(f"✅ تم حفظ {saved_count} علاقة")
    return saved_count


# ============================================
#   3. generate_questions — توليد الأسئلة
# ============================================

def calculate_difficulty_score(bloom_level, concept_difficulty, reasoning_depth=0.5):
    """بتحسب difficulty_score من عوامل متعددة"""

    bloom_scores = {
        "remember": 20,
        "understand": 35,
        "apply": 55,
        "analyze": 70,
        "evaluate": 85,
        "create": 95,
    }

    bloom_score = bloom_scores.get(str(bloom_level).lower(), 50)
    concept_score = concept_difficulty * 100
    reasoning_score = reasoning_depth * 100

    final_score = (
        bloom_score * 0.5 +
        concept_score * 0.3 +
        reasoning_score * 0.2
    )

    return int(final_score)


def get_difficulty_label(difficulty_score):
    """بترجع التصنيف بناءً على الـ score"""
    if difficulty_score <= 35:
        return "easy"
    elif difficulty_score <= 65:
        return "medium"
    else:
        return "hard"


def generate_questions(concepts, pdf_text, source_id, concept_map, questions_per_concept=3):
    """بتولّد أسئلة من المفاهيم"""

    if not concepts:
        print("⚠️ مفيش مفاهيم")
        return []

    if len(pdf_text) > 15000:
        pdf_text = pdf_text[:15000] + "..."

    concepts_list = []
    for c in concepts:
        if not isinstance(c, dict):
            continue
        name = c.get("name", "").strip()
        desc = c.get("description", "")
        importance = c.get("importance", 0.5)
        difficulty = c.get("difficulty", 0.5)
        if name:
            concepts_list.append(
                f"- {name} (importance: {importance}, difficulty: {difficulty}): {desc}"
            )

    concepts_text = "\n".join(concepts_list)
    total_questions = len(concepts) * questions_per_concept

    prompt = f"""إنت مولّد أسئلة تعليمية محترف. ولّد أسئلة اختيارات (MCQ) من المحتوى ده.

📄 المحتوى:
{pdf_text}

━━━━━━━━━━━━━━━

📚 المفاهيم:
{concepts_text}

━━━━━━━━━━━━━━━

🎯 المطلوب:
- ولّد {questions_per_concept} أسئلة لكل مفهوم
- إجمالي: {total_questions} سؤال

⚠️ كل سؤال يكون فيه:
- concept: اسم المفهوم (بالظبط زي ما هو فوق)
- question: نص السؤال (واضح، بدون غموض)
- options: 4 اختيارات (A, B, C, D)
- correct_answer: الإجابة الصحيحة (A / B / C / D)
- explanation: شرح ليه الإجابة صح
- bloom_level: مستوى التفكير
  * "remember" = تذكر (تعريفات)
  * "understand" = فهم (شرح)
  * "apply" = تطبيق (استخدام)
  * "analyze" = تحليل (مقارنة)
  * "evaluate" = تقييم (حكم)
  * "create" = إبداع (تصميم)
- misconception_map: لكل اختيار خاطئ، إيه الفهم الغلط
  * مثال: {{"B": "Confuses X with Y", "C": "Assumes Z"}}

⚠️ مهم جداً:
- الأسئلة تكون من المحتوى، مش من بره
- الإجابة الصحيحة تكون واحدة بس
- الاختيارات الخاطئة تكون معقولة (مش سخيفة)
- متنوع المستويات (سهل، متوسط، صعب)
- متعملش أسئلة مكررة

⚠️ رد بـ JSON فقط:

{{
  "questions": [
    {{
      "concept": "Recursion",
      "question": "What is recursion?",
      "options": {{
        "A": "A function that calls itself",
        "B": "A loop",
        "C": "A variable",
        "D": "A type of array"
      }},
      "correct_answer": "A",
      "explanation": "Recursion is when a function calls itself.",
      "bloom_level": "remember",
      "misconception_map": {{
        "B": "Confuses recursion with loops",
        "C": "Confuses function with variable",
        "D": "Confuses function with data structure"
      }}
    }}
  ]
}}"""

    print(f"📝 جاري توليد الأسئلة ({total_questions} سؤال)...")
    response = ai_generate(prompt, max_tokens=8000, json_mode=True)

    if not response:
        print("❌ فشل توليد الأسئلة")
        return []

    data = extract_json(response)
    if not data or "questions" not in data:
        print("❌ فشل قراءة JSON")
        return []

    questions = data["questions"]

    if not isinstance(questions, list):
        print("❌ الـ questions مش list")
        return []

    # ✅ فلترة: نخلي بس dicts
    questions = [q for q in questions if isinstance(q, dict)]

    print(f"✅ تم توليد {len(questions)} سؤال (صالح)")
    return questions


# ============================================
#   دالة مساعدة: حفظ الأسئلة في Database
# ============================================

def save_questions_to_db(source_id, questions, concepts, concept_map, pdf_text):
    """بتحفظ الأسئلة في Database"""

    saved_count = 0

    concept_difficulty = {}
    for c in concepts:
        if not isinstance(c, dict):
            continue
        name = c.get("name", "").strip()
        difficulty = c.get("difficulty", 0.5)
        if name:
            concept_difficulty[name] = difficulty

    for i, q in enumerate(questions, 1):
        if not isinstance(q, dict):
            continue

        concept_name = q.get("concept", "")
        if not isinstance(concept_name, str):
            concept_name = ""
        concept_name = concept_name.strip()

        question_text = q.get("question", "")
        if not isinstance(question_text, str):
            question_text = ""
        question_text = question_text.strip()

        options = q.get("options", {})
        if not isinstance(options, dict):
            options = {}

        correct_answer = q.get("correct_answer", "")
        if not isinstance(correct_answer, str):
            correct_answer = ""
        correct_answer = correct_answer.strip()

        explanation = q.get("explanation", "")
        bloom_level = q.get("bloom_level", "understand")
        misconception_map = q.get("misconception_map", {})

        if concept_name not in concept_map:
            print(f"  ⚠️ سؤال {i}: المفهوم '{concept_name}' مش موجود")
            continue

        if correct_answer not in options:
            print(f"  ⚠️ سؤال {i}: الإجابة الصحيحة مش في الاختيارات")
            continue

        if len(options) < 4:
            print(f"  ⚠️ سؤال {i}: الاختيارات أقل من 4")
            continue

        concept_diff = concept_difficulty.get(concept_name, 0.5)
        difficulty_score = calculate_difficulty_score(
            bloom_level=bloom_level,
            concept_difficulty=concept_diff,
            reasoning_depth=concept_diff,
        )
        difficulty = get_difficulty_label(difficulty_score)

        concept_id = concept_map[concept_name]

        question_id = save_question(
            source_id=source_id,
            concept_id=concept_id,
            question_text=question_text,
            options=options,
            correct_answer=correct_answer,
            explanation=explanation,
            difficulty=difficulty,
            difficulty_score=difficulty_score,
            bloom_level=bloom_level,
            misconception_map=misconception_map,
        )

        if question_id:
            saved_count += 1
            print(f"  ✅ سؤال {i}: [{difficulty}] {question_text[:50]}...")

    print(f"\n✅ تم حفظ {saved_count} سؤال من {len(questions)}")
    return saved_count


# ============================================
#   4. validate_question — التحقق من السؤال
# ============================================

def validate_question(question, pdf_text, concept_name=None):
    """بتتحقق من صحة السؤال (Deterministic Checks)"""

    # تأكد إن question هي dict
    if not isinstance(question, dict):
        return False, f"السؤال مش dict (نوعه: {type(question).__name__})"

    question_text = question.get("question", "")
    if not isinstance(question_text, str):
        question_text = ""
    question_text = question_text.strip()

    options = question.get("options", {})
    if not isinstance(options, dict):
        return False, "الاختيارات مش dict"

    correct_answer = question.get("correct_answer", "")
    if not isinstance(correct_answer, str):
        correct_answer = ""
    correct_answer = correct_answer.strip()

    explanation = question.get("explanation", "")
    if not isinstance(explanation, str):
        explanation = ""
    explanation = explanation.strip()

    # ===== Check 1: السؤال مش فاضي =====
    if not question_text or len(question_text) < 10:
        return False, "السؤال قصير جداً أو فاضي"

    # ===== Check 2: 4 اختيارات بالظبط =====
    if len(options) != 4:
        return False, f"عدد الاختيارات {len(options)} مش 4"

    # ===== Check 3: الإجابة الصحيحة موجودة =====
    if correct_answer not in options:
        return False, f"الإجابة الصحيحة '{correct_answer}' مش في الاختيارات"

    # ===== Check 4: الاختيارات مش فاضية =====
    for key, value in options.items():
        if not value or len(str(value).strip()) < 2:
            return False, f"الاختيار {key} فاضي أو قصير جداً"

    # ===== Check 5: مفيش اختيارات مكررة =====
    option_values = [str(v).strip().lower() for v in options.values()]
    if len(option_values) != len(set(option_values)):
        return False, "في اختيارات مكررة"

    # ===== Check 6: الشرح موجود =====
    if not explanation or len(explanation) < 10:
        return False, "الشرح قصير جداً أو فاضي"

    # ===== Check 7: الاختيارات معقولة =====
    suspicious_words = ["banana", "موز", "mahmoud", "windows 95", "hello world"]
    for value in options.values():
        value_lower = str(value).lower()
        for word in suspicious_words:
            if word in value_lower:
                return False, f"اختيار فيه كلمة مش منطقية: {word}"

    # ===== Check 8: السؤال فيه علامة استفهام =====
    if "?" not in question_text and "؟" not in question_text:
        return False, "السؤال مش فيه علامة استفهام"

    # ===== Check 9: السؤال مش طويل جداً =====
    if len(question_text) > 500:
        return False, "السؤال طويل جداً (أكثر من 500 حرف)"

    # ===== Check 10: الإجابة مش "all/none of the above" =====
    correct_value = str(options.get(correct_answer, "")).lower()
    if "all of the above" in correct_value or "none of the above" in correct_value:
        return False, "الإجابة الصحيحة مش المفروض تكون 'all/none of the above'"

    # ✅ السؤال صالح
    return True, "OK"


def validate_questions_batch(questions, pdf_text, concepts):
    """بتحقق من مجموعة أسئلة"""

    valid = []
    rejected = 0

    for i, q in enumerate(questions, 1):
        if not isinstance(q, dict):
            rejected += 1
            print(f"  ❌ سؤال {i} اترفض: مش dict (نوعه: {type(q).__name__})")
            continue

        concept_name = q.get("concept", "")
        if not isinstance(concept_name, str):
            concept_name = ""
        concept_name = concept_name.strip()

        is_valid, reason = validate_question(q, pdf_text, concept_name)

        if is_valid:
            valid.append(q)
        else:
            rejected += 1
            print(f"  ❌ سؤال {i} اترفض: {reason}")

    print(f"\n📊 Validation: {len(valid)} صالح، {rejected} مرفوض")
    return valid, rejected


# ============================================
#   5. generate_question_bank — Pipeline الكامل
# ============================================

def generate_question_bank(pdf_text, source_id, max_concepts=15, questions_per_concept=3):
    """Pipeline الكامل لتوليد بنك أسئلة"""

    print(f"\n{'='*60}")
    print(f"🚀 بدء توليد بنك الأسئلة")
    print(f"📄 source_id: {source_id}")
    print(f"{'='*60}\n")

    result = {
        "success": False,
        "concepts_count": 0,
        "relationships_count": 0,
        "questions_count": 0,
        "source_id": source_id,
    }

    # ===== الخطوة 1: استخراج المفاهيم =====
    print("📌 الخطوة 1: استخراج المفاهيم")
    concepts = analyze_content(pdf_text, source_id, max_concepts=max_concepts)

    if not concepts:
        print("❌ فشل استخراج المفاهيم — توقف")
        return result

    result["concepts_count"] = len(concepts)

    # ===== الخطوة 2: حفظ المفاهيم =====
    print("\n📌 الخطوة 2: حفظ المفاهيم في Database")
    concept_map = save_concepts_to_db(source_id, concepts)

    if not concept_map:
        print("❌ فشل حفظ المفاهيم — توقف")
        return result

    # ===== الخطوة 3: بناء العلاقات =====
    print("\n📌 الخطوة 3: بناء العلاقات بين المفاهيم")
    rel_count = build_concept_graph(concepts, pdf_text, source_id, concept_map)
    result["relationships_count"] = rel_count

    # ===== الخطوة 4: توليد الأسئلة =====
    print("\n📌 الخطوة 4: توليد الأسئلة")
    questions = generate_questions(
        concepts, pdf_text, source_id, concept_map,
        questions_per_concept=questions_per_concept
    )

    if not questions:
        print("❌ فشل توليد الأسئلة — توقف")
        return result

    # ===== الخطوة 5: التحقق =====
    print("\n📌 الخطوة 5: التحقق من الأسئلة")
    valid_questions, rejected = validate_questions_batch(questions, pdf_text, concepts)

    if not valid_questions:
        print("❌ كل الأسئلة مرفوضة — توقف")
        return result

    # ===== الخطوة 6: حفظ الأسئلة =====
    print("\n📌 الخطوة 6: حفظ الأسئلة في Database")
    saved_count = save_questions_to_db(
        source_id, valid_questions, concepts, concept_map, pdf_text
    )
    result["questions_count"] = saved_count

    # ===== النتيجة =====
    result["success"] = saved_count > 0

    print(f"\n{'='*60}")
    print(f"✅ خلص توليد بنك الأسئلة")
    print(f"   📚 مفاهيم: {result['concepts_count']}")
    print(f"   🔗 علاقات: {result['relationships_count']}")
    print(f"   📝 أسئلة: {result['questions_count']}")
    print(f"{'='*60}\n")

    return result


# ============================================
#   دوال مساعدة للتكامل مع bot.py
# ============================================

def check_question_bank_exists(source_id):
    """بيتحقق لو بنك الأسئلة موجود"""
    count = count_questions_by_source(source_id)
    return count > 0


def get_source_id_from_file(file_name, user_id):
    """بيعمل source_id من اسم الملف + user_id"""
    clean_name = re.sub(r'[^\w\s-]', '', file_name)
    clean_name = re.sub(r'[-\s]+', '_', clean_name)
    clean_name = clean_name.lower().strip('_')

    if len(clean_name) > 30:
        clean_name = clean_name[:30]

    return f"{clean_name}_{user_id}"