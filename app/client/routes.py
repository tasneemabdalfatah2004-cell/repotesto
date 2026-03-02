from flask import Blueprint, render_template, request, redirect, url_for, session, flash , jsonify
import sqlite3
import json
from config import Config

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
def calculate_matching_score(user_result, designer_result):
    score = 0
    total = 0
    for key in user_result:
        if key in designer_result:
            score += min(user_result[key], designer_result[key])
        total += 1
    return score / total if total > 0 else 0



@client_bp.route("/best_designers", methods=["POST"])
def best_designers():
    try:
        # التأكد من وصول بيانات JSON
        data = request.get_json()
        if not data or "user_analysis" not in data:
            return jsonify({"error": "لا يوجد تحليل للمستخدم."}), 400
            
        user_result = data.get("user_analysis")

        conn = sqlite3.connect("database/db.sqlite")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT id, username, analysis_result FROM users WHERE role='designer'")
        designers = cursor.fetchall()

        best_designers = []
        for d in designers:
            if d['analysis_result']:
                designer_result = json.loads(d['analysis_result'])
                score = calculate_matching_score(user_result, designer_result)
                best_designers.append({
                    "id": d['id'],
                    "username": d['username'],
                    "score": round(score*100, 2)
                })

        # ترتيب حسب أفضل تطابق وأخذ أفضل 3
        best_designers = sorted(best_designers, key=lambda x: x['score'], reverse=True)[:3]
        conn.close()

        # تجهيز قائمة ids و scores لتمريرها في الرابط
        ids_list = [str(d['id']) for d in best_designers]
        scores_list = [str(d['score']) for d in best_designers]

        # إنشاء الرابط للـ GET route
        get_url = url_for(
            "client.show_best_designers",  # اسم الـ GET route
            ids=",".join(ids_list),
            scores=",".join(scores_list)
        )

        print(get_url)

        # إرجاع الرابط كـ JSON
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
                "score": id_to_score.get(d["id"], 0)  # الدرجة المرتبطة بالـ id
            })

        return render_template("client/best_designers.html", designers=designers_list)

    except Exception as e:
        return f"حدث خطأ: {str(e)}", 500