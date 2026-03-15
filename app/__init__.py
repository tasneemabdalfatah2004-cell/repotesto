

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
    add_columns_if_missing(app) 

    # تسجيل Blueprints
    from .auth.routes import auth_bp
    from .home.routes import home_bp
    from .admin.routes import admin_bp
    from .designer.routes import designer_bp
    from .client.routes import client_bp
    from .chat.routes import chat_bp 
    from .ai import ai_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(designer_bp, url_prefix='/designer')
    app.register_blueprint(client_bp, url_prefix='/client')
    app.register_blueprint(chat_bp) 
    app.register_blueprint(ai_bp, url_prefix="/ai")
    with app.app_context():
        try:
            from .utils import auto_analyze_missing_designers
            auto_analyze_missing_designers()
        except Exception as e:
            print(f"⚠️ فشل تشغيل المحلل التلقائي: {e}")
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
        specialty TEXT DEFAULT '',   
        work_type TEXT DEFAULT '',   
        portfolio TEXT DEFAULT '',
        analysis_result TEXT DEFAULT ''

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
    client_id INTEGER NOT NULL,
    designer_id INTEGER,
    design_id INTEGER,
    description TEXT NOT NULL,
    status TEXT DEFAULT 'مفتوح',
    chat_enabled INTEGER DEFAULT 0, -- 0 = لا، 1 = نعم
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    sender_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()
def add_columns_if_missing(app):
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(users);")
    columns = [col[1] for col in cursor.fetchall()]

    if "specialty" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN specialty TEXT DEFAULT ''")
        print("تم إضافة عمود specialty")

    if "work_type" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN work_type TEXT DEFAULT ''")
        print("تم إضافة عمود work_type")


    cursor.execute("PRAGMA table_info(requests);")
    req_columns = [col[1] for col in cursor.fetchall()]

    if "chat_enabled" not in req_columns:
        cursor.execute("ALTER TABLE requests ADD COLUMN chat_enabled INTEGER DEFAULT 0")
        print("تم إضافة عمود chat_enabled لجدول requests")    
    # chat_messages table
    cursor.execute("PRAGMA table_info(chat_messages);")
    chat_columns = [col[1] for col in cursor.fetchall()]

    if "image_path" not in chat_columns:
        cursor.execute(
            "ALTER TABLE chat_messages ADD COLUMN image_path TEXT"
        )
        print("تم إضافة عمود image_path لجدول chat_messages")    

      

    conn.commit()
    conn.close()    