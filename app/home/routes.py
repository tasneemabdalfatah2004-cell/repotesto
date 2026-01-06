from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
import uuid
from werkzeug.utils import secure_filename
from config import Config

home_bp = Blueprint('home', __name__, template_folder='templates')


# ----------------------------
# لوحة التحكم للمصمم
# ----------------------------
@home_bp.route('/')
def home():
    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    portfolio = conn.execute('SELECT * FROM designs ORDER BY id DESC ').fetchall()
    conn.close()

    return render_template('home.html', portfolio=portfolio,)


#-----------------------------
#عرض الطلبات
#-------------------------------
@home_bp.route('/requests')
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