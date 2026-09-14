import os
import google.generativeai as genai
from dotenv import load_dotenv

# تحميل المفتاح من ملف .env
load_dotenv()

# إعداد Gemini بالمفتاح
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# اختيار الموديل
model = genai.GenerativeModel("gemini-3.6-flash")


def translate_text(text, target_language="الإنجليزية"):
    """بيترجم النص للغة المطلوبة"""
    prompt = f"إنت مترجم محترف. ترجم النص ده لـ {target_language} فقط، بدون أي إضافات:\n\n{text}"
    response = model.generate_content(prompt)
    return response.text


def summarize_text(text):
    """بيلخص النص في 3 نقاط"""
    prompt = f"لخص النص ده في 3 نقاط بس، بالعربي:\n\n{text}"
    response = model.generate_content(prompt)
    return response.text


# التجربة
if __name__ == "__main__":
    print("=== خدمة الترجمة والتلخيص ===\n")
    
    text = input("اكتب النص اللي عايز تترجمه أو تلخصه:\n")
    
    print("\n--- الترجمة للإنجليزية ---")
    print(translate_text(text, "الإنجليزية"))
    
    print("\n--- التلخيص ---")
    print(summarize_text(text))