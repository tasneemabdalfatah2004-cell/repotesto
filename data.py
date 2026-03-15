import sqlite3
from config import Config

def check_database_fields():
    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # جلب جميع المصممين
    designers = cursor.execute("SELECT id, username, analysis_result FROM users WHERE role = 'designer'").fetchall()

    print(f"\n{'ID':<5} | {'Username':<20} | {'Status'}")
    print("-" * 45)

    for d in designers:
        # التأكد إذا كان الحقل فارغاً أو يحتوي على بيانات
        status = "✅ موجود (Analyzed)" if d['analysis_result'] and d['analysis_result'].strip() != "" else "❌ فارغ (Not Analyzed)"
        print(f"{d['id']:<5} | {d['username']:<20} | {status}")

    conn.close()

if __name__== "__main__":
    check_database_fields()