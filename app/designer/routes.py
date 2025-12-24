from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from werkzeug.utils import secure_filename
from config import Config

designer_bp = Blueprint('designer', __name__, template_folder='templates')

# التحقق من صلاحية المصمم
def designer_required():
    return 'role' in session and session['role'] == 'designer'


# ----------------------------
# لوحة التحكم للمصمم
# ----------------------------
@designer_bp.route('/')
def dashboard_designer():
    if not designer_required():
        flash('غير مسموح بالدخول!')
        return redirect(url_for('auth.login'))

    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    designer = conn.execute('SELECT * FROM users WHERE id=?', (session['user_id'],)).fetchone()
    portfolio = conn.execute('SELECT * FROM designs WHERE designer_id=?', (session['user_id'],)).fetchall()
    requests_list = conn.execute('SELECT * FROM requests WHERE designer_id=?', (session['user_id'],)).fetchall()
    conn.close()

    return render_template('designer/dashboard_designer.html',
                           designer=designer,
                           portfolio=portfolio,
                           requests=requests_list)


# ----------------------------
# إضافة عمل جديد
# ----------------------------
@designer_bp.route('/add_design', methods=['GET', 'POST'])
def add_design():
    if not designer_required():
        flash('غير مسموح بالدخول!')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        design_type = request.form.get('design_type', '')
        style = request.form.get('style', '')

        if 'image' not in request.files:
            flash('لم يتم رفع أي صورة')
            return redirect(request.url)

        file = request.files['image']
        if file.filename == '':
            flash('لم يتم اختيار صورة')
            return redirect(request.url)

        # تحقق من صيغة الصورة
        if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS:
            filename = secure_filename(file.filename)
            filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
            file.save(filepath)
            db_path = f"uploads/{filename}"

            conn = sqlite3.connect(Config.DATABASE)
            conn.execute('INSERT INTO designs (designer_id, title, description, image_path) VALUES (?,?,?,?)',
                         (session['user_id'], title, description, db_path))
            conn.commit()
            conn.close()

            flash('تم إضافة العمل بنجاح!')
            return redirect(url_for('designer.dashboard_designer'))
        else:
            flash('نوع الملف غير مسموح!')
            return redirect(request.url)

    return render_template('designer/add_design.html')


# ----------------------------
# متابعة الطلبات الخاصة بالمصمم
# ----------------------------
@designer_bp.route('/requests')
def designer_requests():
    if not designer_required():
        flash('غير مسموح بالدخول!')
        return redirect(url_for('auth.login'))

    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    requests_list = conn.execute('SELECT * FROM requests WHERE designer_id=?', (session['user_id'],)).fetchall()
    conn.close()

    return render_template('designer/requests_designer.html', requests=requests_list)


# ----------------------------
# فتح المحادثة مع العميل
# ----------------------------
@designer_bp.route('/chat/<int:request_id>')
def open_chat(request_id):
    if not designer_required():
        flash('غير مسموح بالدخول!')
        return redirect(url_for('auth.login'))

    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    req = conn.execute('SELECT * FROM requests WHERE id=? AND designer_id=?',
                       (request_id, session['user_id'])).fetchone()
    conn.close()

    if req:
        return render_template('designer/chat_designer.html', request=req)
    flash('الطلب غير موجود!')
    return redirect(url_for('designer.designer_requests'))


# ----------------------------
# تسليم التصميم النهائي
# ----------------------------
@designer_bp.route('/submit/<int:request_id>', methods=['POST'])
def submit_design(request_id):
    if not designer_required():
        flash('غير مسموح بالدخول!')
        return redirect(url_for('auth.login'))

    conn = sqlite3.connect(Config.DATABASE)
    conn.execute('UPDATE requests SET status="مكتمل" WHERE id=? AND designer_id=?',
                 (request_id, session['user_id']))
    conn.commit()
    conn.close()
    flash('تم تسليم التصميم بنجاح!')
    return redirect(url_for('designer.designer_requests'))


# ----------------------------
# تعديل الملف الشخصي للمصمم
# ----------------------------
@designer_bp.route('/profile', methods=['GET', 'POST'])
def profile_designer():
    if not designer_required():
        flash('غير مسموح بالدخول!')
        return redirect(url_for('auth.login'))

    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row

    if request.method == 'POST':
        username = request.form['username']
        bio = request.form['bio']
        portfolio = request.form['portfolio']

        conn.execute('UPDATE users SET username=?, bio=?, portfolio=? WHERE id=?',
                     (username, bio, portfolio, session['user_id']))
        conn.commit()
        conn.close()

        flash('تم حفظ التغييرات بنجاح!')
        return redirect(url_for('designer.profile_designer'))

    designer = conn.execute('SELECT * FROM users WHERE id=?', (session['user_id'],)).fetchone()
    portfolio = conn.execute('SELECT * FROM designs WHERE designer_id=? ORDER BY id DESC;', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('designer/profile_designer.html', designer=designer, portfolio=portfolio)    