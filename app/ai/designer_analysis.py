import json
from google import genai
from google.genai import types
import os
import re

# مفتاح Gemini API
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set.")

# إنشاء العميل
client = genai.Client(api_key=GEMINI_API_KEY)

# النظام (Prompt) لتحليل المصمم
DESIGNER_PROMPT = """
أنت نظام ذكي لتحليل شخصية المصممين.

سيتم إعطاؤك:
- معلومات المصمم النصية
- صور من أعماله

حلل الأسلوب ونوع التصميم.


أخرج النتيجة بصيغة JSON فقط بدون أي شرح.

القيم من 0 إلى 1:
0.0 = غير موجود
0.25 = ضعيف
0.5 = متوسط
0.75 = واضح
1.0 = أساسي

الخصائص:

**design_type**: logo, poster, mockup, ui, visual_identity, banner, social_post, flyer, brochure, packaging
**sub_type**: awareness_post, opening_post, promotional_post, educational_post, product_showcase, event_announcement, brand_intro
**style**: modern, classic, minimal, luxury, playful, technical, elegant, bold, flat, 3d, futuristic, vintage
**colors/mood**: bright_colors, dark_colors, pastel_colors, monochrome, warm_tones, cool_tones, high_contrast, soft_contrast
**audience**: kids, teenagers, young_adults, professionals, businesses, general_public
**project_field**: education, technology, healthcare, real_estate, ecommerce, finance, food, fashion, entertainment, nonprofit
**platform_or_usage**: mobile_app, web_app, dashboard, landing_page, social_media, print, presentation
**special_requirements**: responsive, animation, branding_guidelines, accessibility, multilanguage, fast_loading, seo_friendly

"""

def analyze_designer(designer_text, image_path=[]):
    
    parts = [
        {"text": DESIGNER_PROMPT + "\n\nالمعلومات:\n" + designer_text}
    ]

    
    # إضافة الصور
    for img_path in image_path:
        with open(img_path, "rb") as f:
            parts.append(
                types.Part.from_bytes(
                    data=f.read(),
                    mime_type="image/png"
                )
            )
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            {
               "role": "user",
               "parts": parts
            }
        ]    
    )    
    # دمج جميع النصوص الناتجة
    output_text = ""
    for part in getattr(response, "parts", []):
        if getattr(part, "text", None):
            output_text += part.text

    print("RAW OUTPUT FROM MODEL:")
    print(output_text)

    # استخراج أول كائن JSON صالح من النص
    match = re.search(r"\{.*\}", output_text, re.DOTALL)
    if not match:
        print("لم يتم العثور على JSON صالح في إخراج النموذج:")
        print(output_text)
        return None

    json_text = match.group()
    try:
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        print("خطأ عند تحويل JSON:", e)
        print("النص الخام:", json_text)
        return None