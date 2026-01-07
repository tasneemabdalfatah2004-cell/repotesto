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
        return redirect(url_for('home.home'))

    return render_template('designer/add_design.html')

# ----------------------------
# تعديل الملف الشخصي للمصمم
# ----------------------------
@designer_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    if not designer_required():
        flash('غير مسموح بالدخول!')
        return redirect(url_for('auth.login'))

    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == 'POST':
        # حقل username لا نعدله لأنه مُحدد عند التسجيل
        bio = request.form.get('bio', '')
        specialty = request.form.get('specialty', '')
        work_type = request.form.get('work_type', '')

        cursor.execute(
            '''
            UPDATE users
            SET bio = ?, specialty = ?, work_type = ?
            WHERE id = ?
            ''',
            (bio, specialty, work_type, session['user_id'])
        )
        conn.commit()
        flash('تم حفظ التغييرات بنجاح!')

    designer = cursor.execute(
        'SELECT * FROM users WHERE id=?',
        (session['user_id'],)
    ).fetchone()

    portfolio = cursor.execute(
        'SELECT * FROM designs WHERE designer_id=? ORDER BY id DESC',
        (session['user_id'],)
    ).fetchall()

    conn.close()

    return render_template(
        'designer/profile.html',
        designer=designer,
        portfolio=portfolio
    )
#---------------------------------
#تفاصيل المشروع
#-------------------------------------
@designer_bp.route('/design/<int:design_id>')
def design_details(design_id):
    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row

    # جلب بيانات المشروع
    design = conn.execute(
        'SELECT d.*, u.username as designer_name FROM designs d '
        'JOIN users u ON d.designer_id = u.id '
        'WHERE d.id = ?',
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
#-----------------------------
#عرض الطلبات
#-------------------------------
@designer_bp.route('/requests')
def designer_requests():
    if not designer_required():
        flash('غير مسموح بالدخول')
        return redirect(url_for('auth.login'))

    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row

    requests = conn.execute("""
        SELECT 
            r.id,
            r.description,
            r.status,
            u.username AS client_name,
            d.title AS design_title
        FROM requests r
        JOIN users u ON r.client_id = u.id
        LEFT JOIN designs d ON r.design_id = d.id
        WHERE r.designer_id = ?
        ORDER BY r.created_at DESC
    """, (session['user_id'],)).fetchall()

    conn.close()

    return render_template(
        'designer/requests.html',
        requests=requests
    )

@designer_bp.route('/accept_request/<int:request_id>')
def accept_request(request_id):
    if not designer_required():
        flash('غير مسموح بالدخول')
        return redirect(url_for('auth.login'))

    conn = sqlite3.connect(Config.DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE requests
        SET status = 'مقبول', chat_enabled = 1
        WHERE id = ?
    """, (request_id,))

    conn.commit()
    conn.close()

    flash("تم قبول الطلب! المحادثة مع العميل مفتوحة الآن.")
    return redirect(url_for('designer.designer_requests'))


@designer_bp.route('/reject_request/<int:request_id>')
def reject_request(request_id):
    if not designer_required():
        flash('غير مسموح بالدخول')
        return redirect(url_for('auth.login'))

    conn = sqlite3.connect(Config.DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE requests
        SET status = 'مرفوض'
        WHERE id = ?
    """, (request_id,))

    conn.commit()
    conn.close()

    flash("تم رفض الطلب.")
    return redirect(url_for('designer.designer_requests'))
    #------------------------------
    #عرض الصفحة للمستخدم
    #----------------------------
@designer_bp.route('/profile/<int:designer_id>')
def profile_view(designer_id):
    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # جلب معلومات المصمم
    designer = cursor.execute(
        'SELECT * FROM users WHERE id=? AND role="designer"',
        (designer_id,)
    ).fetchone()

    if not designer:
        flash('المصمم غير موجود!')
        return redirect(url_for('home.home'))

    # جلب أعمال المصمم
    portfolio = cursor.execute(
        'SELECT * FROM designs WHERE designer_id=? ORDER BY id DESC',
        (designer_id,)
    ).fetchall()

    conn.close()

    # عرض الصفحة بدون حقول تعديل، فقط للعرض
    return render_template('designer/profile_view.html', designer=designer, portfolio=portfolio)    
