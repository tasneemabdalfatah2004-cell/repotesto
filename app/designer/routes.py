from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
import uuid
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
# إضافة عمل جديد (متوافق مع عدة صور)
# ----------------------------

@designer_bp.route('/add_design', methods=['GET', 'POST'])
def add_design():
    if not designer_required():
        flash('غير مسموح بالدخول!')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        images = request.files.getlist('images')

        if not images or images[0].filename == '':
            flash('لم يتم اختيار أي صورة')
            return redirect(request.url)

        conn = sqlite3.connect(Config.DATABASE)
        cursor = conn.cursor()

        design_id = None

        for i, file in enumerate(images):
            ext = file.filename.rsplit('.',1)[1].lower()
            if ext not in Config.ALLOWED_EXTENSIONS:
                flash('أحد الملفات غير مدعوم')
                conn.close()
                return redirect(request.url)

            # اسم فريد لكل صورة
            unique_filename = f"{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
            file.save(filepath)
            db_path = f"uploads/{unique_filename}"

            if i == 0:
                # الصورة الأولى = غلاف المشروع
                cursor.execute(
                    'INSERT INTO designs (designer_id, title, description, image_path) VALUES (?,?,?,?)',
                    (session['user_id'], title, description, db_path)
                )
                design_id = cursor.lastrowid

            # كل الصور تخزن في design_images
            cursor.execute(
                'INSERT INTO design_images (design_id, image_path) VALUES (?,?)',
                (design_id, db_path)
            )

        conn.commit()
        conn.close()
        flash('تم إضافة العمل بنجاح!')
        return redirect(url_for('designer.dashboard_designer'))

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
#---------------------------------
#تفاصيل المشروع
#-------------------------------------
@designer_bp.route('/design/<int:design_id>')
def design_details(design_id):
    if not designer_required():
        flash('غير مسموح بالدخول!')
        return redirect(url_for('auth.login'))

    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row

    # جلب بيانات المشروع
    design = conn.execute(
        'SELECT * FROM designs WHERE id = ?',
        (design_id,)
    ).fetchone()

    # جلب كل الصور المرفقة
    images = conn.execute(
        'SELECT image_path FROM design_images WHERE design_id = ?',
        (design_id,)
    ).fetchall()

    conn.close()

    return render_template(
        'designer/design_details.html',
        design=design,
        images=images
    )    