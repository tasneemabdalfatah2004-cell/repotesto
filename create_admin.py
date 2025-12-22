import sqlite3
import os
from werkzeug.security import generate_password_hash

DATABASE = 'database/db.sqlite'

# إنشاء مجلد database إذا لم يكن موجود
if not os.path.exists('database'):
    os.makedirs('database')

conn = sqlite3.connect(DATABASE)
c = conn.cursor()

# إنشاء جدول المستخدمين إذا لم يكن موجود
c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        email TEXT NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )
''')

# إضافة عمود active إذا لم يكن موجود
try:
    c.execute('ALTER TABLE users ADD COLUMN active INTEGER DEFAULT 1')
except sqlite3.OperationalError:
    pass  # العمود موجود بالفعل

# التحقق إذا كان المدير موجود مسبقًا
c.execute('SELECT * FROM users WHERE role=?', ('admin',))
existing = c.fetchone()
if existing:
    print("المدير موجود مسبقًا في قاعدة البيانات.")
else:
    # بيانات المدير
    username = "Admin"
    email = "admin@example.com"
    password = generate_password_hash("admin123")  # كلمة المرور: admin123
    role = "admin"

    c.execute('INSERT INTO users (username,email,password,role,active) VALUES (?,?,?,?,?)',
              (username,email,password,role,1))
    conn.commit()
    print("تم إنشاء المدير بنجاح!")

conn.close()