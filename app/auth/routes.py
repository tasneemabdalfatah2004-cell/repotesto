from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

# ✅ تعريف Blueprint بشكل صحيح
auth_bp = Blueprint('auth', __name__, template_folder='templates')

# ----------------------------
# تسجيل الدخول
# ----------------------------
@auth_bp.route('/', methods=['GET','POST'])
@auth_bp.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect(Config.DATABASE)
        conn.row_factory = sqlite3.Row
        user = conn.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            if user['active'] == 0:
                flash('حسابك معطل من قبل المدير.')
                return redirect(url_for('auth.login'))

            session['user_id'] = user['id']
            session['role'] = user['role']
            session['username'] = user['username']
            flash('تم تسجيل الدخول بنجاح!')

            # إعادة التوجيه حسب الدور
            if user['role'] == 'admin':
                return redirect(url_for('admin.dashboard_admin'))
            elif user['role'] == 'designer':
                return redirect(url_for('designer.dashboard_designer'))
            else:
                return redirect(url_for('client.dashboard_client'))
        else:
            flash('البريد الإلكتروني أو كلمة المرور غير صحيحة!')

    return render_template('auth/login.html')


# ----------------------------
# تسجيل حساب جديد
# ----------------------------
@auth_bp.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']

        conn = sqlite3.connect(Config.DATABASE)
        # التحقق إذا كان البريد موجود مسبقًا
        existing_user = conn.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
        if existing_user:
            flash('البريد الإلكتروني مستخدم مسبقًا!')
            conn.close()
            return redirect(url_for('auth.register'))

        conn.execute('INSERT INTO users (username,email,password,role,active) VALUES (?,?,?,?,1)',
                     (username,email,password,role))
        conn.commit()
        conn.close()
        flash('تم إنشاء الحساب بنجاح!')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


# ----------------------------
# تسجيل الخروج
# ----------------------------
@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('تم تسجيل الخروج!')
    return redirect(url_for('auth.login'))