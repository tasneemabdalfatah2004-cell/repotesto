from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sqlite3
from config import Config

chat_bp = Blueprint(
    'chat',
   __name__,
    template_folder='templates'
)
@chat_bp.route('/chat/<int:request_id>', methods=['GET', 'POST'])
def chat(request_id):
    if 'user_id' not in session:
        flash("يرجى تسجيل الدخول")
        return redirect(url_for('auth.login'))

    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row

    req = conn.execute(
        'SELECT * FROM requests WHERE id=?',
        (request_id,)
    ).fetchone()

    if not req or req['status'] != 'مقبول':
        conn.close()
        flash('لا يمكن فتح المحادثة')
        return redirect(url_for('home.home'))

    # التحقق من الصلاحية
    if session['user_id'] not in (req['client_id'], req['designer_id']):
        conn.close()
        flash('غير مسموح')
        return redirect(url_for('home.home'))

    # تحديد الطرف الآخر
    if session['user_id'] == req['client_id']:
        other = conn.execute(
            'SELECT username FROM users WHERE id=?',
            (req['designer_id'],)
        ).fetchone()
    else:
        other = conn.execute(
            'SELECT username FROM users WHERE id=?',
            (req['client_id'],)
        ).fetchone()

    # إرسال رسالة
    if request.method == 'POST':
        message = request.form.get('message', '').strip()
        if message:
            conn.execute(
                'INSERT INTO chat_messages (request_id, sender_id, message) VALUES (?,?,?)',
                (request_id, session['user_id'], message)
            )
            conn.commit()

    # جلب الرسائل
    messages = conn.execute("""
        SELECT cm.*, u.username
        FROM chat_messages cm
        JOIN users u ON cm.sender_id = u.id
        WHERE cm.request_id=?
        ORDER BY cm.id ASC
    """, (request_id,)).fetchall()

    conn.close()

    return render_template(
        'chat/chat.html',
        messages=messages,
        other_user_name=other['username']
    )
