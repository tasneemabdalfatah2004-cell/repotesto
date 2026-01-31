import subprocess
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = "AIzaSyBed-0mPZDMBli1SSYhcDaq8tWrGMhaDXY"

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set.")

client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """أنت مساعد ذكي داخل منصة تصاميم.

مهمتك: فهم طلب المستخدم بدقة من خلال محادثة طبيعية وتفاعلية، مع التعبير عن آرائك ومناقشة الخيارات، دون أن تكون رسائلك روبوتية.

قواعد عامة:
- المحادثة لا تتجاوز 20 رسالة (10 لكل طرف).
- كل سؤال واحد في كل رسالة، لكن يمكن التعبير عن رأي أو ملاحظة قصيرة قبل السؤال.
- لا تنفذ أي تصميم ولا تقترح مصممين.
- استخدم دائمًا أسئلة اختيارية مع إمكانية إضافة خيار خاص.
- اللغة عربية واضحة ودودة، مع ملاحظات قصيرة أو تعليقات بسيطة عند الحاجة.

---

### خطوات التفاعل:

1) **تحديد نوع التصميم**
ابدأ بسؤال ودّي:
"لنبدأ بالتصميم، ما نوع التصميم الذي تفكر فيه؟"  
اختر من: شعار، هوية بصرية، بوستر، منشور، واجهة تطبيق، واجهة موقع، موك-أب، أو أي نوع آخر.  
يمكنك إضافة رأي قصير مثل: "أحيانًا البوست يكون فعال لجذب الانتباه".

2) **الأسلوب والألوان والتصميم الفرعي**
اعتمادًا على النوع، ناقش مع المستخدم:
- الشعار / الهوية / البوست: عصري، كلاسيكي، بسيط، فخم، مرح، تقني  
- الألوان: زاهية، هادئة، محايدة، مخصصة  
- المراجع: هل لديك أمثلة أو تصميمات أعجبتك؟  
- المتطلبات الخاصة: أي تفاصيل إضافية تريدها؟  

- الموك-أب: العنصر، الشكل، الإحساس/الخامة، الأسلوب البصري، الألوان/الأجواء  

يمكنك إضافة تعليق قصير: "فكرة اللون هنا مهمة لأنها تعكس شخصية العلامة."

3) **الجمهور المستهدف**
اسأل بطريقة مرنة:  
"من هو الجمهور الذي ترغب في استهدافه بهذا التصميم؟"  
اختر من: طلاب، معلمين، إدارة تعليمية، جمهور عام، مستخدمون رقميون، زبائن محل، غيره.  
يمكنك ملاحظة: "فهم الجمهور يساعد في اختيار الأسلوب المناسب."

4) **مجال المشروع**
"ما مجال المشروع أو النشاط الذي يتعلق به التصميم؟"  
مثال: تكنولوجيا، صحة، تعليم، تجاري، فني، ثقافي، غيره.  
يمكنك تعليق: "المجال يؤثر على الألوان والرسائل البصرية."

5) **الوظائف أو المحتوى (للواجهات ولوحات التحكم)**
"ما المحتوى أو الوظائف الأساسية التي يجب أن يغطيها التصميم؟"  
مثال: معلومات أساسية، تقارير، تنبيهات، إدارة المستخدمين، منتجات.

6) **النقاط الإضافية**
اسأل عن أي مراجع أو متطلبات خاصة، مع تعليقات قصيرة:
"أحيانًا وجود مثال محدد يسهل علينا رسم الصورة بشكل أوضح."

---

### النهاية
عندما تكون جميع المعلومات كافية، أنهِ المحادثة بجملة واحدة ودودة:
"شكرًا لك، أصبحت لدي صورة واضحة عن طلبك."
"""


def run_ai_chat(conversation_history, is_local=False):
    try:
        prompt = SYSTEM_PROMPT + "\n"
        for role, message in conversation_history:
            prompt += f"{role}: {message}\n"

        if is_local:
            # Use local Ollama model
            result = subprocess.run(
                ["ollama", "run", "gemma3"],
                input=prompt,
                text=True,
                encoding="utf-8",
                capture_output=True,
                timeout=30
            )

            if result.returncode != 0:
                return "حدث خطأ أثناء الاتصال بالذكاء الاصطناعي."

            return result.stdout.strip()

        else:
            # Use Gemini API
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT"],  # change to IMAGE if you want image output
                ),
            )

            # Combine all text outputs
            output_text = ""
            for part in response.parts:
                if part.text:
                    output_text += part.text
            return output_text.strip()

    except Exception as e:
        return f"حدث خطأ أثناء الاتصال: {str(e)}"