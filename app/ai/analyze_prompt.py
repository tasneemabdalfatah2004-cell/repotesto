import re
import subprocess
import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set.")

client = genai.Client(api_key=GEMINI_API_KEY)

# هذا هو الـ SYSTEM PROMPT لتحليل المحادثة واستخراج المعايير
EXTRACT_PROMPT = """
أنت نظام ذكي لتحليل محادثة تصميم.

مهمتك: تحليل المحادثة واستخراج خصائص التصميم على شكل مؤشرات رقمية.

أخرج النتيجة بصيغة JSON فقط، كل صفة مفتاح، والقيمة رقم من 0 إلى 1 يمثل مدى حضور الصفة:
0.0 = غير موجودة، 0.25 = ضعيف، 0.5 = متوسط، 0.75 = واضح، 1.0 = أساسية.
إذا لم تُذكر الصفة، ضع قيمتها 0.0.

الخصائص تشمل:

**design_type**: logo, poster, mockup, ui, visual_identity, banner, social_post, flyer, brochure, packaging
**sub_type**: awareness_post, opening_post, promotional_post, educational_post, product_showcase, event_announcement, brand_intro
**style**: modern, classic, minimal, luxury, playful, technical, elegant, bold, flat, 3d, futuristic, vintage
**colors/mood**: bright_colors, dark_colors, pastel_colors, monochrome, warm_tones, cool_tones, high_contrast, soft_contrast
**audience**: kids, teenagers, young_adults, professionals, businesses, general_public
**project_field**: education, technology, healthcare, real_estate, ecommerce, finance, food, fashion, entertainment, nonprofit
**platform_or_usage**: mobile_app, web_app, dashboard, landing_page, social_media, print, presentation
**special_requirements**: responsive, animation, branding_guidelines, accessibility, multilanguage, fast_loading, seo_friendly
مثال عن شكل الخرج
{
"design_type": {"logo": 1.0, "poster": 0.0, "mockup": 0.0, "ui": 0.0, "visual_identity": 0.0, "banner": 0.0, "social_post": 0.0, "flyer": 0.0, "brochure": 0.0, "packaging": 0.0}
نفس الشيء بالنسبة ل sub_type وباقي الخيارات
}

"""

def analyze_conversation(conversation_history, is_local=False):
    """
    conversation_history: قائمة من tuples بالشكل [(role, message), ...]
    role = "المستخدم" أو "الذكاء"
    message = نص الرسالة
    """
    # بناء الـ prompt النهائي
    prompt = EXTRACT_PROMPT + "\n\nالمحادثة:\n"
    for role, message in conversation_history:
        prompt += f"{role}: {message}\n"

    try:
        if is_local:
            # استخدم نموذج Gemma3 محليًا
            result = subprocess.run(
                ["ollama", "run", "gemma3"],
                input=prompt,
                text=True,
                encoding="utf-8",
                capture_output=True,
                timeout=30
            )

            print(result)

            if result.returncode != 0:
                print("حدث خطأ أثناء الاتصال بالذكاء الاصطناعي.")
                return None

            # محاولة تحويل الناتج إلى JSON
            try:
                return json.loads(result.stdout.strip())
            except json.JSONDecodeError:
                print("تعذر تحليل الإخراج إلى JSON. الإخراج الخام:")
                print(result.stdout.strip())
                return None

        else:
            # استخدم Gemini API
            response = client.models.generate_content(
                model="gemma-3-27b-it",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT"],  # نريد نص لتفسيره كـ JSON
                ),
            )

            # دمج جميع النصوص
            output_text = ""
            for part in response.parts:
                if part.text:
                    output_text += part.text
                    
            # محاولة تحويل الناتج إلى JSON
            try:
                # Extract first JSON object between { ... }
                match = re.search(r"\{.*\}", output_text, re.DOTALL)

                if not match:
                    print("No JSON object found.")
                    print(output_text)
                    return None

                json_text = match.group()
                print(json_text)
                return json.loads(json_text)
            except json.JSONDecodeError:
                print("تعذر تحليل إخراج Gemini API إلى JSON. الإخراج الخام:")
                print(output_text.strip())
                return None

    except subprocess.TimeoutExpired:
        print("انتهت مهلة الاتصال بالذكاء الاصطناعي.")
        return None
    except Exception as e:
        print(f"حدث خطأ: {str(e)}")
        return None