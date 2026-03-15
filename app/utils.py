import sqlite3
import json
import os
import time
from flask import current_app

# استيراد الدالة من المسار اللي حددته: app/ai/routes.py
try:
    from app.ai.routes import analyze_designer
except ImportError:
    # محاولة بديلة في حال كان التشغيل من داخل المجلد
    from .ai.routes import analyze_designer

def auto_analyze_missing_designers():
    """وظيفة تبحث عن المصممين غير المحللين وتقوم بتحديثهم تلقائياً عند تشغيل السيرفر"""
    
    # الحصول على مسار قاعدة البيانات من إعدادات Flask
    db_path = current_app.config['DATABASE']
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. جلب المصممين الذين ينقصهم التحليل (المصممين الـ 8 اللي طلعوا عندك)
    # نستخدم الحقول المتوفرة: bio, specialty, work_type
    query = """
        SELECT id, username, bio, specialty, work_type 
        FROM users 
        WHERE role = 'designer' 
        AND (analysis_result IS NULL OR analysis_result = '' OR analysis_result = '{}')
    """
    missing_designers = cursor.execute(query).fetchall()

    if not missing_designers:
        # إذا كان الجميع محللين، لا نفعل شيئاً
        return 

    print(f"\n🤖 [نظام التحليل التلقائي]: وجدنا {len(missing_designers)} مصممين بانتظار المعالجة...")

    for designer in missing_designers:
        d_id = designer['id']
        name = designer['username']
        
        # تجهيز النص الذي سيقرأه الذكاء الاصطناعي
        designer_info = f"""
        المصمم: {name}
        التخصص: {designer['specialty']}
        النبذة: {designer['bio']}
        نوع العمل: {designer['work_type']}
        """

        # تحديد مسار المجلد الذي يحتوي على صور المصمم
        # نعتمد على ID المصمم في اسم المجلد (تأكد أن هذا يطابق نظامك)
        image_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], f"designer_{d_id}")
        
        images = []
        if os.path.exists(image_folder):
            # نأخذ أول 3 صور فقط للتحليل لضمان السرعة وتجنب التكلفة
            images = [
                os.path.join(image_folder, f) 
                for f in os.listdir(image_folder) 
                if f.lower().endswith(('.png', '.jpg', '.jpeg'))
            ][:3]

        try:
            print(f"🎨 جاري إرسال بيانات المصمم '{name}' لـ Gemini...")
            
            # استدعاء دالة الذكاء الاصطناعي
            result_json = analyze_designer(designer_info, images)

            if result_json:
                # حفظ النتيجة في قاعدة البيانات كـ JSON نصي
                cursor.execute(
                    "UPDATE users SET analysis_result = ? WHERE id = ?", 
                    (json.dumps(result_json), d_id)
                )
                conn.commit()
                print(f"✅ تم تحديث ملف المصمم: {name} بنجاح.")
                
                # فاصل زمني بسيط (ثانية واحدة) لتجنب حظر الـ API (Rate Limit)
                time.sleep(1) 
            else:
                print(f"⚠️ تحذير: لم يرجع الـ AI نتيجة صالحة للمصمم {name}")

        except Exception as e:
            print(f"❌ خطأ غير متوقع أثناء معالجة {name}: {e}")

    conn.close()
    print("🏁 [نظام التحليل]: انتهت عملية التحديث التلقائي.\n")