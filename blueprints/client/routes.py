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
    if not client_required():
        flash('غير مسموح بالدخول!')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        description = request.form['description']
        designer_id = request.form.get('designer_id')  # يمكن اختيار مصمم محدد لاحقًا

        conn = sqlite3.connect(Config.DATABASE)
        conn.execute('INSERT INTO requests (client_id, designer_id, description) VALUES (?,?,?)',
                     (session['user_id'], designer_id, description))
        conn.commit()
        conn.close()

        flash('تم إرسال الطلب بنجاح!')
        return redirect(url_for('client.dashboard_client'))

    return render_template('client/new_request.html')


# ----------------------------
# فتح دردشة مع المصمم
# ----------------------------
@client_bp.route('/chat/<int:request_id>')
def open_chat(request_id):
    if not client_required():
        flash('غير مسموح بالدخول!')
        return redirect(url_for('auth.login'))

    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    req = conn.execute('SELECT * FROM requests WHERE id=? AND client_id=?',
                       (request_id, session['user_id'])).fetchone()
    conn.close()

    if req:
        return render_template('client/chat_client.html', request=req)
    flash('الطلب غير موجود!')
    return redirect(url_for('client.dashboard_client'))


# ----------------------------
# استلام التصميم النهائي
# ----------------------------
@client_bp.route('/receive/<int:request_id>', methods=['POST'])
def receive_design(request_id):
    if not client_required():
        flash('غير مسموح بالدخول!')
        return redirect(url_for('auth.login'))

    # في هذه المرحلة مجرد تأكيد الاستلام
    flash('تم استلام التصميم النهائي!')
    return redirect(url_for('client.dashboard_client'))