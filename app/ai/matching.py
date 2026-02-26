import json
import sqlite3
from config import Config


def calculate_similarity(client_json, designer_json):
    total_score = 0
    count = 0

    for category in client_json:
        if category not in designer_json:
            continue

        for key, client_value in client_json[category].items():
            designer_value = designer_json.get(category, {}).get(key, 0)
            similarity = 1 - abs(client_value - designer_value)
            total_score += similarity
            count += 1

    if count == 0:
        return 0

    return round(total_score / count, 3)


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