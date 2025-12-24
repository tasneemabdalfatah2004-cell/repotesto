from flask import Blueprint, render_template, session, redirect, url_for, flash
import sqlite3
from config import Config

admin_bp = Blueprint('admin', __name__, template_folder='templates')

# ----------------------------
# لوحة التحكم الرئيسية للمدير
# ----------------------------
@admin_bp.route('/')
def dashboard_admin():
    if 'role' not in session or session['role'] != 'admin':
        flash('غير مسموح بالدخول!')
        return redirect(url_for('auth.login'))

    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row

    # جميع المستخدمين
    users = conn.execute('SELECT * FROM users').fetchall()

    # إحصائيات
    designers_count = conn.execute('SELECT COUNT(*) FROM users WHERE role="designer"').fetchone()[0]
    clients_count = conn.execute('SELECT COUNT(*) FROM users WHERE role="client"').fetchone()[0]
    requests_count = conn.execute('SELECT COUNT(*) FROM requests').fetchone()[0]

    conn.close()

    return render_template('admin/dashboard_admin.html',
                           users=users,
                           designers_count=designers_count,
                           clients_count=clients_count,
                           requests_count=requests_count)


# ----------------------------
# تفعيل / تعطيل مستخدم
# ----------------------------
@admin_bp.route('/toggle_user/<int:user_id>')
def toggle_user(user_id):
    if 'role' not in session or session['role'] != 'admin':
        flash('غير مسموح بالدخول!')
        return redirect(url_for('auth.login'))

    conn = sqlite3.connect(Config.DATABASE)
    conn.execute('UPDATE users SET active = CASE WHEN active=1 THEN 0 ELSE 1 END WHERE id=?', (user_id,))
    conn.commit()
    conn.close()
    flash('تم تغيير حالة المستخدم!')
    return redirect(url_for('admin.dashboard_admin'))


# ----------------------------
# حذف مستخدم
# ----------------------------
@admin_bp.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    if 'role' not in session or session['role'] != 'admin':
        flash('غير مسموح بالدخول!')
        return redirect(url_for('auth.login'))

    conn = sqlite3.connect(Config.DATABASE)
    conn.execute('DELETE FROM users WHERE id=?', (user_id,))
    conn.commit()
    conn.close()
    flash('تم حذف المستخدم!')
    return redirect(url_for('admin.dashboard_admin'))