import subprocess
import json

# هذا هو الـ SYSTEM PROMPT لتحليل المحادثة واستخراج المعايير
EXTRACT_PROMPT = """
أنت نظام ذكي لتحليل محادثة تصميم.

مهمتك:
تحليل المحادثة بين المستخدم والمساعد
واستخراج المعايير النهائية للتصميم.

أخرج النتيجة بصيغة JSON فقط بدون أي شرح.

المفاتيح المطلوبة:
- design_type          # نوع التصميم: شعار، بوستر، موك-أب، واجهة، هوية بصرية، إلخ
- sub_type             # النوع الفرعي إذا وجد (مثلاً: بوست توعوي، بوست افتتاح)
- style                # الأسلوب: عصري، كلاسيكي، بسيط، فخم، مرح، تقني
- colors               # الألوان أو الأجواء
- audience             # الجمهور المستهدف
- project_field        # مجال المشروع
- platform_or_usage    # إذا كان لتطبيق، موقع، لوحة تحكم، أو موك-أب عنصر محدد
- special_requirements  # أي متطلبات خاصة

إذا لم تُذكر قيمة، ضع null.
"""

def analyze_conversation(conversation_history):
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
        # تنفيذ الأمر لتشغيل نموذج Gemma3
        result = subprocess.run(
            ["ollama", "run", "gemma3"],
            input=prompt,
            text=True,
            encoding="utf-8",
            capture_output=True,
            timeout=30  # لتجنب الانتظار الطويل
        )

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

    except subprocess.TimeoutExpired:
        print("انتهت مهلة الاتصال بالذكاء الاصطناعي.")
        return None
    except Exception as e:
        print(f"حدث خطأ: {str(e)}")
        return None
