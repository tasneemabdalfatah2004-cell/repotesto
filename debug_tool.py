import json
import sqlite3
from config import Config

def check_designer_matching_v2(target_name):
    try:
        conn = sqlite3.connect(Config.DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        designer = cursor.execute("SELECT username, analysis_result FROM users WHERE username = ?", (target_name,)).fetchone()
        if not designer: return

        designer_json = json.loads(designer["analysis_result"])

        # طلب العميل (كما هو)
        client_request_json = {
            "design_type": {"poster": 1.0},
            "style": {"modern": 1.0}
        }

        print(f"\n📊 تقرير فحص المطابقة (التنسيق الجديد): {target_name}")
        print("-" * 75)

        total_score, total_weight = 0, 0

        for category, fields in client_request_json.items():
            # التعديل الجوهري: البحث عن الفئة الأصلية أو الفئة التي تنتهي بـ _values
            # إذا لم يجد 'design_type' كـ dict، سيبحث عن 'design_type_values'
            designer_category = designer_json.get(category, {})
            if not isinstance(designer_category, dict):
                designer_category = designer_json.get(f"{category}_values", {})

            for key, client_value in fields.items():
                designer_value = designer_category.get(key, 0)
                
                similarity = 1 - abs(client_value - designer_value)
                weight = 3 if category == "design_type" else 1
                
                total_score += similarity * weight
                total_weight += weight
                
                print(f"{category:<18} | {key:<15} | العميل: {client_value:<5} | سارة: {designer_value:<5} | التشابه: {similarity:.2f}")

        final_score = round(total_score / total_weight, 3) if total_weight > 0 else 0
        print("-" * 75)
        print(f"⭐️ النتيجة النهائية: {final_score}")

    except Exception as e:
        print(f"❌ خطأ: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_designer_matching_v2("سارة محمد")