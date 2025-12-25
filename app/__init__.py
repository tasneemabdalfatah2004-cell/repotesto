

from flask import Flask
from config import Config
import os
import sqlite3

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # إنشاء مجلدات مهمة
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), '..', 'database'), exist_ok=True)

    # تهيئة قاعدة البيانات إذا لم تكن موجودة
    init_db(app)

    # تسجيل Blueprints
    from .auth.routes import auth_bp
    from .admin.routes import admin_bp
    from .designer.routes import designer_bp
    from .client.routes import client_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(designer_bp, url_prefix='/designer')
    app.register_blueprint(client_bp, url_prefix='/client')

    return app


def init_db(app):
    conn = sqlite3.connect(app.config['DATABASE'])
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
        designer_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        image_path TEXT NOT NULL
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