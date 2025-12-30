from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sqlite3
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