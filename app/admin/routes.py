from flask import Blueprint, render_template, session, redirect, url_for, flash, request
import sqlite3
import os
from config import Config

admin_bp = Blueprint('admin', __name__, template_folder='templates')


# ----------------------------
# لوحة تحكم المدير
# ----------------------------
@admin_bp.route('/')
def dashboard_admin():
    if 'role' not in session or session['role'] != 'admin':
        flash('غير مسموح بالدخول!')
        return redirect(url_for('auth.login'))

    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row

    users = conn.execute("SELECT * FROM users WHERE role='client'").fetchall()
    
    # الإحصائيات
    users_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    designers_count = conn.execute("SELECT COUNT(*) FROM users WHERE role='designer'").fetchone()[0]
    # إضافة حساب العملاء
    clients_count = conn.execute("SELECT COUNT(*) FROM users WHERE role='client'").fetchone()[0]
    requests_count = conn.execute("SELECT COUNT(*) FROM requests").fetchone()[0]
    designs_count = conn.execute("SELECT COUNT(*) FROM designs").fetchone()[0]

    conn.close()

    return render_template(
        "admin/dashboard_admin.html",
        users=users,
        users_count=users_count,
        designers_count=designers_count,
        clients_count=clients_count, # مررناها لهون
        requests_count=requests_count,
        designs_count=designs_count
    )

# ----------------------------
# لوحة تحكم المدير مصممين
# ----------------------------
@admin_bp.route('/designers')
def dashboard_admin_designers():
    if 'role' not in session or session['role'] != 'admin':
        flash('غير مسموح بالدخول!')
        return redirect(url_for('auth.login'))

    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row

    users = conn.execute("SELECT * FROM users WHERE role='designer'").fetchall()
    
    # الإحصائيات
    users_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    designers_count = conn.execute("SELECT COUNT(*) FROM users WHERE role='designer'").fetchone()[0]
    # إضافة حساب العملاء
    clients_count = conn.execute("SELECT COUNT(*) FROM users WHERE role='client'").fetchone()[0]
    requests_count = conn.execute("SELECT COUNT(*) FROM requests").fetchone()[0]
    designs_count = conn.execute("SELECT COUNT(*) FROM designs").fetchone()[0]

    conn.close()

    return render_template(
        "admin/dashboard_admin_designers.html",
        users=users,
        users_count=users_count,
        designers_count=designers_count,
        clients_count=clients_count, # مررناها لهون
        requests_count=requests_count,
        designs_count=designs_count
    )

# ----------------------------
# لوحة تحكم المدير طلبات'
# ----------------------------
@admin_bp.route('/requests')
def dashboard_admin_requests():
    if 'role' not in session or session['role'] != 'admin':
        flash('غير مسموح بالدخول!')
        return redirect(url_for('auth.login'))

    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row

    requests = conn.execute("""
        SELECT 
            r.*,
            client.username AS client_username,
            designer.username AS designer_username,
            d.title AS design_title
        FROM requests r
        LEFT JOIN users client ON r.client_id = client.id
        LEFT JOIN users designer ON r.designer_id = designer.id
        LEFT JOIN designs d ON r.design_id = d.id;
        """).fetchall()
    
    # الإحصائيات
    users_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    designers_count = conn.execute("SELECT COUNT(*) FROM users WHERE role='designer'").fetchone()[0]
    # إضافة حساب العملاء
    clients_count = conn.execute("SELECT COUNT(*) FROM users WHERE role='client'").fetchone()[0]
    requests_count = conn.execute("SELECT COUNT(*) FROM requests").fetchone()[0]
    designs_count = conn.execute("SELECT COUNT(*) FROM designs").fetchone()[0]

    conn.close()

    return render_template(
        "admin/dashboard_admin_requests.html",
        requests=requests,
        users_count=users_count,
        designers_count=designers_count,
        clients_count=clients_count, # مررناها لهون
        requests_count=requests_count,
        designs_count=designs_count
    )

# ----------------------------
# تفعيل / تعطيل مستخدم
# ----------------------------
@admin_bp.route('/toggle_user/<int:user_id>')
def toggle_user(user_id):

    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('auth.login'))

    conn = sqlite3.connect(Config.DATABASE)

    conn.execute(
        'UPDATE users SET active = CASE WHEN active=1 THEN 0 ELSE 1 END WHERE id=?',
        (user_id,)
    )

    conn.commit()
    conn.close()

    flash('تم تغيير حالة المستخدم')
    return redirect(url_for('admin.dashboard_admin'))


# ----------------------------
# حذف مستخدم
# ----------------------------
@admin_bp.route('/delete_user/<int:user_id>')
def delete_user(user_id):

    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('auth.login'))

    conn = sqlite3.connect(Config.DATABASE)

    conn.execute(
        'DELETE FROM users WHERE id=?',
        (user_id,)
    )

    conn.commit()
    conn.close()

    flash('تم حذف المستخدم')
    return redirect(url_for('admin.dashboard_admin'))



# ----------------------------
# حذف طلب'
# ----------------------------
@admin_bp.route('/delete_request/<int:request_id>')
def delete_request(request_id):

    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('auth.login'))

    conn = sqlite3.connect(Config.DATABASE)

    conn.execute(
        'DELETE FROM requests WHERE id=?',
        (request_id,)
    )

    conn.commit()
    conn.close()

    flash('تم حذف الطلب')
    return redirect(url_for('admin.dashboard_admin_requests'))


# ----------------------------
# عرض صفحة المصمم
# ----------------------------
@admin_bp.route('/designer_profile/<int:user_id>')
def view_designer_profile(user_id):

    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('auth.login'))

    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row

    designer = conn.execute(
        'SELECT * FROM users WHERE id=? AND role="designer"',
        (user_id,)
    ).fetchone()

    if not designer:
        flash('المصمم غير موجود')
        return redirect(url_for('admin.dashboard_admin'))

    designs = conn.execute(
        'SELECT * FROM designs WHERE designer_id=?',
        (user_id,)
    ).fetchall()

    conn.close()

    return render_template(
        'admin/view_designer.html',
        designer=designer,
        designs=designs
    )
# ----------------------------
# حذف تصميم (نسخة محسنة)
# ----------------------------
@admin_bp.route('/delete_design/<int:design_id>')
def delete_design(design_id):

    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('auth.login'))

    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row

    # جلب البيانات قبل الحذف
    design = conn.execute(
        'SELECT * FROM designs WHERE id=?',
        (design_id,)
    ).fetchone()

    if design:
        designer_id = design['designer_id']
        image_path = design['image_path']

        # 1. حذف السجل من قاعدة البيانات (الأولوية هنا)
        conn.execute('DELETE FROM designs WHERE id=?', (design_id,))
        
        # 2. تصفير تحليل المصمم
        conn.execute("UPDATE users SET analysis_result='' WHERE id=?", (designer_id,))
        
        # 3. حفظ التغييرات فوراً في قاعدة البيانات
        conn.commit() 

        # 4. حذف الملف المادي من السيرفر (بعد التأكد من حذف السجل)
        # استخدمنا image_path المخزن مباشرة لضمان المسار الصحيح
        if image_path:
            # إذا كان المسار مخزن كاملاً أو نسبياً، تأكد من الوصول إليه
            # سنحاول حذف الملف بناءً على المسار المخزن
            full_path = os.path.join(os.getcwd(), image_path) # أو حسب إعداداتك
            if os.path.exists(full_path):
                os.remove(full_path)
            elif os.path.exists(os.path.join(Config.UPLOAD_FOLDER, f"designer_{designer_id}", os.path.basename(image_path))):
                os.remove(os.path.join(Config.UPLOAD_FOLDER, f"designer_{designer_id}", os.path.basename(image_path)))

        flash('تم حذف التصميم نهائياً من قاعدة البيانات والسيرفر')
    else:
        flash('عذراً، التصميم غير موجود')

    conn.close()

    # التوجيه للرئيسية لضمان رؤية النتيجة فوراً
    return redirect(url_for('home.home'))

