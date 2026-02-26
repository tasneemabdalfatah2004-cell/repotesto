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
    """
    هذا الروت يستدعى بعد انتهاء تحليل محادثة العميل مع الـ AI.
    request.json يجب أن يحتوي على:
    { "user_analysis": {...} }  # ناتج analyze_conversation
    """
    try:
        user_result = request.json.get("user_analysis")
        if not user_result:
            return jsonify({"error": "لا يوجد تحليل للمستخدم."}), 400

        conn = sqlite3.connect("database/db.sqlite")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # جلب جميع المصممين
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
                    "score": round(score*100, 2)  # نسبة مئوية
                })

        # فرز حسب أفضل تطابق
        best_designers = sorted(best_designers, key=lambda x: x['score'], reverse=True)[:3]

        conn.close()
        return render_template("client/best_designers.html", designers=best_designers)

    except Exception as e:
        return jsonify({"error": str(e)}), 500