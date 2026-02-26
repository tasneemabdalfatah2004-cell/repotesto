import json
from google import genai
from google.genai import types

# مفتاح Gemini API
GEMINI_API_KEY = "AIzaSyCHw1kJwkr1RbbUSNB4_GS-HLpdJBwbGWE"

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set.")

# إنشاء العميل
client = genai.Client(api_key=GEMINI_API_KEY)

# النظام (Prompt) لتحليل المصمم
DESIGNER_PROMPT = """
أنت نظام ذكي لتحليل شخصية المصممين.

المصدر:
- التخصص
- نبذة المصمم
- طابع الأعمال
- أسماء المشاريع
- وصف المشاريع إن وجد

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

def analyze_designer(designer_text):
    """
    designer_text: نص شامل لكل ما ذكر أعلاه عن المصمم
    """
    prompt = DESIGNER_PROMPT + "\n\nالنص:\n" + designer_text

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["TEXT"]
        )
    )

    output_text = ""
    for part in response.parts:
        if part.text:
            output_text += part.text
    print(output_text)
    # نرجع JSON جاهز للاستخدام
    return json.loads(output_text.strip())