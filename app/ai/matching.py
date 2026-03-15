import json
import sqlite3
from config import Config


def calculate_similarity(client_json, designer_json):
    total_score = 0
    total_weight=0


      for category, fields in client_json.items():
        # محاولة جلب الفئة مباشرة أو جلب النسخة التي تنتهي بـ _values
        designer_category = designer_json.get(category, {})
        if not isinstance(designer_category, dict):
            designer_category = designer_json.get(f"{category}_values", {})

        # إذا كانت الفئة لا تزال غير موجودة كـ Dictionary، نعتبرها فارغة
        if not isinstance(designer_category, dict):
            designer_category = {}

        for key, client_value in fields.items():
            # جلب قيمة المصمم، وإذا لم توجد نعتبرها 0
            designer_value = designer_category.get(key, 0)
            
            # حساب التشابه
            similarity = 1 - abs(client_value - designer_value)
            
            # إعطاء وزن أعلى (3) لنوع التصميم لأنه الأهم في المطابقة
            weight = 3 if category == "design_type" else 1

            total_score += similarity * weight
            total_weight += weight

    if total_weight == 0:
        return 0

    return round(total_score / total_weight, 3)


def match_designers(client_analysis_json, limit=3):
    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    designers = cursor.execute("""
        SELECT id, username, analysis_result
        FROM users
        WHERE role = 'designer'
          AND analysis_result IS NOT NULL
          AND analysis_result != ''
    """).fetchall()

    results = []

    for designer in designers:
        try:
            designer_json = json.loads(designer["analysis_result"])
            score = calculate_similarity(client_analysis_json, designer_json)

            results.append({
                "designer_id": designer["id"],
                "username": designer["username"],
                "score": score
            })

        except Exception as e:
            print("خطأ:", e)

    conn.close()

    results.sort(key=lambda x: x["score"], reverse=True)

    return results[:limit]