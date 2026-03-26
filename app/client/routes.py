from flask import Blueprint, render_template, request, redirect, url_for, session, flash , jsonify
import sqlite3
import json
from config import Config
import math

client_bp = Blueprint('client', __name__, template_folder='templates')

# التحقق من صلاحية العميل
def client_required():
    return 'role' in session and session['role'] == 'client'

# ----------------------------
# لوحة التحكم للعميل
# ----------------------------
@client_bp.route('/')
def dashboard_client():
    if not client_required():
        flash('غير مسموح بالدخول!')
        return redirect(url_for('auth.login'))

    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    requests_list = conn.execute('SELECT * FROM requests WHERE client_id=?', (session['user_id'],)).fetchall()
    conn.close()

    return render_template('client/dashboard_client.html',
                           client_name=session['username'],
                           requests=requests_list)


# ----------------------------
# إرسال طلب تصميم جديد
# ----------------------------
@client_bp.route('/new_request', methods=['GET', 'POST'])
def new_request():
    if 'user_id' not in session:
        flash('يرجى تسجيل الدخول لإرسال طلب')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        description = request.form['description']
        designer_id = request.form.get('designer_id')
        design_id = request.form.get('design_id')

        conn = sqlite3.connect(Config.DATABASE)
        conn.execute(
            '''
            INSERT INTO requests (client_id, designer_id, design_id, description)
            VALUES (?,?,?,?)
            ''',
            (session['user_id'], designer_id, design_id, description)
        )
        conn.commit()
        conn.close()

        flash('تم إرسال الطلب بنجاح')
        return redirect(url_for('home.home'))
    
    designer_id = request.args.get('designer_id')
    design_id = request.args.get('design_id')

    return render_template('client/new_request.html', designer_id=designer_id, design_id=design_id)


@client_bp.route('/profile', methods=['GET'])
def profile():
    if not client_required():
        flash('غير مسموح بالدخول!')
        return redirect(url_for('auth.login'))

    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row

    client = conn.execute(
        'SELECT * FROM users WHERE id=?',
        (session['user_id'],)
    ).fetchone()

    conn.close()
    return render_template(
        'profile.html',
        client=client
    )
@client_bp.route('/requests')
def requests_view():
    if not client_required():
        flash("غير مسموح بالدخول!")
        return redirect(url_for('auth.login'))

    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row

    requests = conn.execute("""
        SELECT
            r.id,
            r.description,
            r.status,
            r.created_at,
            u.username AS designer_name
        FROM requests r
        LEFT JOIN users u ON r.designer_id = u.id
        WHERE r.client_id = ?
        ORDER BY r.created_at DESC
    """, (session['user_id'],)).fetchall()

    conn.close()
    return render_template('client/client_requests.html', requests=requests)   

def category_similarity(user_values, designer_values):
    """
    Similarity داخل كل category.
    نقيس overlap مقارنة بما طلبه المستخدم.
    """
    keys = set(user_values.keys()) | set(designer_values.keys())
    user_total = sum(float(user_values.get(k, 0)) for k in keys)
    
    if user_total == 0:
        return 0.0

    overlap = sum(
        min(float(user_values.get(k, 0)), float(designer_values.get(k, 0)))
        for k in keys
    )

    return overlap / user_total


def calculate_matching_score(user_result, designer_result):
    weights = {
        "design_type": 10.0,   # أهم 10 مرات
        "sub_type": 1.0,
        "style": 1.0,
        "colors/mood": 1.0,
        "colors_mood": 1.0,
        "audience": 1.0,
        "project_field": 1.0,
        "platform_or_usage": 1.0,
        "special_requirements": 1.0,
    }

    total_weight = 0.0
    weighted_score = 0.0

    for category, user_values in user_result.items():
        designer_values = designer_result.get(category)

        if designer_values is None and category == "colors/mood":
            designer_values = designer_result.get("colors_mood", {})

        if not isinstance(user_values, dict) or not isinstance(designer_values, dict):
            continue

        sim = category_similarity(user_values, designer_values)
        weight = weights.get(category, 1.0)

        weighted_score += sim * weight
        total_weight += weight

    return weighted_score / total_weight if total_weight > 0 else 0.0


def smart_scale_scores(raw_scores, min_pct=5, max_pct=95):
    """
    نعيد توزيع النتائج حسب ترتيبها داخل المجموعة.
    هذا ليس hard-coded على 1=95 و2=75 و3=50،
    بل حسب rank + curve ناعمة.
    """
    n = len(raw_scores)
    if n == 0:
        return []

    if n == 1:
        return [round(max_pct, 2)]

    ranked = sorted(enumerate(raw_scores), key=lambda x: x[1], reverse=True)
    final_scores = [0.0] * n

    # منحنى ناعم: الأفضل يأخذ قيمة أعلى بشكل واضح
    # وكلما زاد عدد المرشحين، تصبح التوزيعة أكثر توازنًا
    gamma = 0.85 + (0.35 / math.log(n + 1.5))

    for rank, (idx, _) in enumerate(ranked):
        p = 1 - (rank / (n - 1))   # الأفضل = 1 ، الأسوأ = 0
        curved = p ** gamma
        curved = curved * curved * (3 - 2 * curved)  # smoothstep
        final_scores[idx] = min_pct + curved * (max_pct - min_pct)

    return [round(max(min_pct, min(max_pct, s)), 2) for s in final_scores]


@client_bp.route("/best_designers", methods=["POST"])
def best_designers():
    try:
        data = request.get_json()
        if not data or "user_analysis" not in data:
            return jsonify({"error": "لا يوجد تحليل للمستخدم."}), 400
            
        user_result = data.get("user_analysis")

        conn = sqlite3.connect("database/db.sqlite")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT id, username, analysis_result FROM users WHERE role='designer'")
        designers = cursor.fetchall()

        best_designers_list = [] # تغيير الاسم لتجنب التداخل
        for d in designers:
            if d['analysis_result']:
                try:
                    designer_result = json.loads(d['analysis_result'])
                    
                    # استدعاء دالة الحساب
                    print("user_result")
                    print(user_result)
                    print("designer_result")
                    print(designer_result)
                    final_score = calculate_matching_score(user_result, designer_result)
                    
                    best_designers_list.append({
                        "id": d['id'],
                        "username": d['username'],
                        "score": round(final_score * 100, 2)
                    })
                except Exception as e:
                    print(f"فشل في معالجة المصمم {d['username']}: {e}")
                    continue

        # الترتيب الآن سيتم بين أرقام (Floats) ولن يظهر الخطأ
        sorted_designers = sorted(best_designers_list, key=lambda x: x['score'], reverse=True)[:3]
        conn.close()

        # تجهيز البيانات للرابط
        ids_list = [str(d['id']) for d in sorted_designers]
        scores_list = [str(d['score']) for d in sorted_designers]

        get_url = url_for(
            "client.show_best_designers",
            ids=",".join(ids_list),
            scores=",".join(scores_list)
        )

        return jsonify({"url": get_url})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500
    

@client_bp.route("/best_designers", methods=["GET"])
def show_best_designers():
    """
    GET route لاستعراض أفضل المصممين مع درجات التطابق.
    تمرير المعرفات والدرجات عبر query params:
    ids=3,7,12
    scores=85,72,68
    """
    try:
        ids_param = request.args.get("ids")       # "3,7,12"
        scores_param = request.args.get("scores") # "85,72,68"

        if not ids_param or not scores_param:
            return "لم يتم تحديد المعرفات أو الدرجات.", 400

        ids_list = [int(i) for i in ids_param.split(",") if i.strip().isdigit()]
        scores_list = [float(s) for s in scores_param.split(",") if s.strip()]

        if len(ids_list) != len(scores_list):
            return "عدد المعرفات لا يطابق عدد الدرجات.", 400

        # جلب بيانات المصممين من قاعدة البيانات
        conn = sqlite3.connect("database/db.sqlite")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        placeholder = ",".join(["?"] * len(ids_list))
        query = f"SELECT id, username, bio, specialty, work_type FROM users WHERE id IN ({placeholder})"
        cursor.execute(query, ids_list)
        designers = cursor.fetchall()
        conn.close()

        # دمج المعلومات مع درجات التطابق
        designers_list = []
        id_to_score = dict(zip(ids_list, scores_list))

        for d in designers:
            designers_list.append({
                "id": d["id"],
                "username": d["username"],
                "bio": d["bio"],
                "specialty": d["specialty"],
                "work_type": d["work_type"],
                "score": id_to_score.get(d["id"], 0.0) # تأكد أنها Float
            })

        designers_list.sort(key=lambda x: x['score'], reverse=True)

        return render_template("client/best_designers.html", designers=designers_list)

    except Exception as e:
        return f"حدث خطأ: {str(e)}", 500