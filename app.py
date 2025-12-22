from flask import Flask, render_template, redirect, url_for, request, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = 'super-secret-key'
DATABASE = 'database/db.sqlite'

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('database', exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

# إنشاء قاعدة البيانات والجداول إذا لم تكن موجودة
conn = sqlite3.connect(DATABASE)
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    email TEXT NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL,
    active INTEGER DEFAULT 1,
    bio TEXT DEFAULT '',
    portfolio TEXT DEFAULT ''
)
''')
c.execute('''
CREATE TABLE IF NOT EXISTS designs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    designer_id INTEGER,
    title TEXT,
    description TEXT,
    image_path TEXT
)
''')
c.execute('''
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER,
    designer_id INTEGER,
    description TEXT,
    status TEXT DEFAULT 'مفتوح'
)
''')
conn.commit()
conn.close()

# ----------------------------
# تسجيل حساب جديد
# ----------------------------
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']
        conn = sqlite3.connect(DATABASE)
        conn.execute('INSERT INTO users (username,email,password,role,active) VALUES (?,?,?,?,1)',
                     (username,email,password,role))
        conn.commit()
        conn.close()
        flash('تم إنشاء الحساب بنجاح!')
        return redirect(url_for('login'))
    return render_template('register.html')

# ----------------------------
# تسجيل الدخول
# ----------------------------
@app.route('/', methods=['GET','POST'])
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        user = conn.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            if user['active']==0:
                flash('حسابك معطل من قبل المدير.')
                return redirect(url_for('login'))
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['username'] = user['username']
            if user['role']=='admin':
                return redirect(url_for('dashboard_admin'))
            elif user['role']=='designer':
                return redirect(url_for('dashboard_designer'))
            else:
                return redirect(url_for('dashboard_client'))
        else:
            flash('البريد الإلكتروني أو كلمة المرور غير صحيحة!')
    return render_template('login.html')

# ----------------------------
# تسجيل الخروج
# ----------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ----------------------------
# Dashboard المدير
# ----------------------------
@app.route('/admin')
def dashboard_admin():
    if 'role' in session and session['role']=='admin':
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        users = conn.execute('SELECT * FROM users').fetchall()
        requests_count = conn.execute('SELECT COUNT(*) FROM requests').fetchone()[0]
        conn.close()
        return render_template('dashboard_admin.html', users=users, requests_count=requests_count)
    return redirect(url_for('login'))

# تفعيل / تعطيل حساب
@app.route('/toggle_user/<int:user_id>')
def toggle_user(user_id):
    if 'role' in session and session['role']=='admin':
        conn = sqlite3.connect(DATABASE)
        conn.execute('UPDATE users SET active=CASE WHEN active=1 THEN 0 ELSE 1 END WHERE id=?',(user_id,))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard_admin'))
    return redirect(url_for('login'))

# حذف مستخدم
@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    if 'role' in session and session['role']=='admin':
        conn = sqlite3.connect(DATABASE)
        conn.execute('DELETE FROM users WHERE id=?',(user_id,))
        conn.commit()
        conn.close()
        flash('تم حذف الحساب بنجاح!')
        return redirect(url_for('dashboard_admin'))
    return redirect(url_for('login'))

# ----------------------------
# Dashboard المصمم
# ----------------------------
@app.route('/designer')
def dashboard_designer():
    if 'role' in session and session['role']=='designer':
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        designer = conn.execute('SELECT * FROM users WHERE id=?',(session['user_id'],)).fetchone()
        portfolio = conn.execute('SELECT * FROM designs WHERE designer_id=?',(session['user_id'],)).fetchall()
        requests_list = conn.execute('SELECT * FROM requests WHERE designer_id=?',(session['user_id'],)).fetchall()
        conn.close()
        return render_template('dashboard_designer.html', designer=designer, portfolio=portfolio, requests=requests_list)
    return redirect(url_for('login'))

# إضافة عمل جديد
@app.route('/designer/add_design', methods=['GET','POST'])
def add_design():
    if 'role' in session and session['role']=='designer':
        if request.method=='POST':
            title = request.form['title']
            description = request.form['description']
            if 'image' not in request.files:
                flash('لم يتم رفع أي صورة'); return redirect(request.url)
            file = request.files['image']
            if file.filename=='':
                flash('لم يتم اختيار صورة'); return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                db_path = f"uploads/{filename}"
                conn = sqlite3.connect(DATABASE)
                conn.execute('INSERT INTO designs (designer_id,title,description,image_path) VALUES (?,?,?,?)',
                             (session['user_id'],title,description,db_path))
                conn.commit()
                conn.close()
                flash('تم إضافة العمل بنجاح!')
                return redirect(url_for('dashboard_designer'))
            else:
                flash('نوع الملف غير مسموح!')
                return redirect(request.url)
        return render_template('add_design.html')
    return redirect(url_for('login'))

# الطلبات الخاصة بالمصمم
@app.route('/designer/requests')
def designer_requests():
    if 'role' in session and session['role']=='designer':
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        requests_list = conn.execute('SELECT * FROM requests WHERE designer_id=?',(session['user_id'],)).fetchall()
        conn.close()
        return render_template('requests_designer.html', requests=requests_list)
    return redirect(url_for('login'))

# فتح المحادثة
@app.route('/designer/chat/<int:request_id>')
def open_chat(request_id):
    if 'role' in session and session['role']=='designer':
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        req = conn.execute('SELECT * FROM requests WHERE id=? AND designer_id=?',(request_id, session['user_id'])).fetchone()
        conn.close()
        if req:
            return render_template('chat_designer.html', request=req)
    return redirect(url_for('designer_requests'))

# تسليم التصميم
@app.route('/designer/submit/<int:request_id>', methods=['POST'])
def submit_design(request_id):
    if 'role' in session and session['role']=='designer':
        conn = sqlite3.connect(DATABASE)
        conn.execute('UPDATE requests SET status="مكتمل" WHERE id=? AND designer_id=?',(request_id, session['user_id']))
        conn.commit()
        conn.close()
        flash('تم تسليم التصميم بنجاح!')
    return redirect(url_for('designer_requests'))

# ----------------------------
# Dashboard العميل
# ----------------------------
@app.route('/client')
def dashboard_client():
    if 'role' in session and session['role']=='client':
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        requests_list = conn.execute('SELECT * FROM requests WHERE client_id=?',(session['user_id'],)).fetchall()
        conn.close()
        return render_template('dashboard_client.html', client_name=session['username'], requests=requests_list)
    return redirect(url_for('login'))
# -------------------------------
# ملف شخصي للمصمم
# -------------------------------
@app.route('/designer/profile', methods=['GET','POST'])
def profile_designer():
    if 'role' in session and session['role'] == 'designer':
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row

        if request.method == 'POST':
            username = request.form['username']
            bio = request.form['bio']
            portfolio = request.form['portfolio']

            conn.execute(
                'UPDATE users SET username=?, bio=?, portfolio=? WHERE id=?',
                (username, bio, portfolio, session['user_id'])
            )
            conn.commit()
            conn.close()

            flash('تم حفظ التغييرات بنجاح!')
            return redirect(url_for('profile_designer'))

        designer = conn.execute(
            'SELECT * FROM users WHERE id=?',
            (session['user_id'],)
        ).fetchone()
        conn.close()

        return render_template('profile_designer.html', designer=designer)

    return redirect(url_for('login'))
# ----------------------------
# تشغيل التطبيق
# ----------------------------
if __name__=='__main__':
    app.run(debug=True)