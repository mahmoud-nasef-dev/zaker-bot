import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
import arabic_reshaper
from bidi.algorithm import get_display

from config import DEVELOPER_NAME, DEVELOPER_USERNAME, BOT_NAME, BOT_USERNAME

# ===== الخط العربي =====
FONT_PATH = os.path.join("fonts", "Amiri-Regular.ttf")
FONT_NAME = "Amiri"

if os.path.exists(FONT_PATH):
    pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))
else:
    print(f"⚠️ تحذير: الخط مش موجود في {FONT_PATH}")
    FONT_NAME = "Helvetica"

# ===== الألوان =====
PRIMARY = HexColor("#2563EB")
SECONDARY = HexColor("#F97316")
DARK = HexColor("#1F2937")
LIGHT = HexColor("#F3F4F6")
WHITE = HexColor("#FFFFFF")


def ar(text):
    """بتظبط النص العربي عشان يظهر صح في PDF"""
    if not text:
        return ""
    reshaped = arabic_reshaper.reshape(str(text))
    return get_display(reshaped)


def clean_markdown(text):
    """بتنضف النص من علامات Markdown و LaTeX"""
    if not text:
        return ""
    text = text.replace("$\\rightarrow$", "←")
    text = text.replace("$\\leftarrow$", "→")
    text = text.replace("$\\Rightarrow$", "⇒")
    text = text.replace("$\\to$", "→")
    text = text.replace("$", "")
    text = text.replace("**", "")
    if not text.startswith("*"):
        text = text.replace("*", "")
    return text


def get_styles():
    """بترجع أنماط النصوص"""
    return {
        "title": ParagraphStyle(
            "Title",
            fontName=FONT_NAME,
            fontSize=24,
            textColor=PRIMARY,
            alignment=TA_CENTER,
            spaceAfter=10,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle",
            fontName=FONT_NAME,
            fontSize=14,
            textColor=DARK,
            alignment=TA_CENTER,
            spaceAfter=20,
        ),
        "section": ParagraphStyle(
            "Section",
            fontName=FONT_NAME,
            fontSize=16,
            textColor=PRIMARY,
            alignment=TA_RIGHT,
            spaceBefore=12,
            spaceAfter=8,
        ),
        "body": ParagraphStyle(
            "Body",
            fontName=FONT_NAME,
            fontSize=12,
            textColor=DARK,
            alignment=TA_RIGHT,
            leading=20,
            spaceAfter=6,
        ),
        "footer": ParagraphStyle(
            "Footer",
            fontName=FONT_NAME,
            fontSize=10,
            textColor=SECONDARY,
            alignment=TA_CENTER,
        ),
    }


def add_header_footer(canvas, doc):
    """بترسم الهيدر والفوتر على كل صفحة"""
    canvas.saveState()

    # Header
    canvas.setFillColor(PRIMARY)
    canvas.rect(0, A4[1] - 2 * cm, A4[0], 2 * cm, fill=1, stroke=0)

    canvas.setFillColor(WHITE)
    canvas.setFont(FONT_NAME, 16)
    canvas.drawCentredString(A4[0] / 2, A4[1] - 1.2 * cm, ar(f"{BOT_NAME} - مساعدك الدراسي"))

    # Footer
    canvas.setFillColor(LIGHT)
    canvas.rect(0, 0, A4[0], 1.5 * cm, fill=1, stroke=0)

    canvas.setFillColor(DARK)
    canvas.setFont(FONT_NAME, 9)
    canvas.drawCentredString(
        A4[0] / 2,
        0.9 * cm,
        ar(f"{DEVELOPER_NAME}  •  {DEVELOPER_USERNAME}  •  {BOT_USERNAME}"),
    )

    canvas.restoreState()


def create_pdf_report(analysis_text, user_name, output_path="report.pdf"):
    """بتنشئ ملف PDF من النص اللي Gemini رجعه"""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=3 * cm,
        bottomMargin=2 * cm,
    )

    styles = get_styles()
    story = []

    # ===== العنوان =====
    story.append(Paragraph(ar("تحليل المحاضرة"), styles["title"]))
    story.append(
        Paragraph(ar(f"أُعدّ خصيصاً للطالب: {user_name}"), styles["subtitle"])
    )
    story.append(
        Paragraph(
            ar(f"التاريخ: {datetime.now().strftime('%Y-%m-%d')}"),
            styles["subtitle"],
        )
    )
    story.append(Spacer(1, 0.5 * cm))

    # ===== المحتوى =====
    lines = analysis_text.split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            story.append(Spacer(1, 0.2 * cm))
            continue

        line = clean_markdown(line)

        # عنوان
        if line.endswith(":") or ":" in line[:30]:
            story.append(Paragraph(ar(line), styles["section"]))
        # نقطة
        elif line.startswith("-") or line.startswith("•") or line.startswith("*"):
            content = line.lstrip("-•* ").strip()
            story.append(Paragraph(ar(f"• {content}"), styles["body"]))
        # رقم
        elif len(line) > 2 and line[0].isdigit() and line[1] in ".-":
            story.append(Paragraph(ar(line), styles["body"]))
        # عادي
        else:
            story.append(Paragraph(ar(line), styles["body"]))

    # ===== نهاية الملف =====
    story.append(Spacer(1, 1 * cm))
    story.append(
        Table(
            [[""]],
            colWidths=[A4[0] - 4 * cm],
            rowHeights=[0.05 * cm],
            style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), SECONDARY)]),
        )
    )
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(ar(f"تم إنشاء هذا التقرير بواسطة {BOT_NAME}"), styles["footer"]))

    doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)

    return output_path