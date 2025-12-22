import sqlite3
import os

DATABASE = 'database/db.sqlite'

# إنشاء مجلد database إذا لم يكن موجود
if not os.path.exists('database'):
    os.makedirs('database')

conn = sqlite3.connect(DATABASE)
c = conn.cursor()

# إضافة عمود bio إذا لم يكن موجود
try:
    c.execute("ALTER TABLE users ADD COLUMN bio TEXT DEFAULT ''")
except sqlite3.OperationalError:
    pass  # العمود موجود مسبقًا

# إضافة عمود portfolio إذا لم يكن موجود
try:
    c.execute("ALTER TABLE users ADD COLUMN portfolio TEXT DEFAULT ''")
except sqlite3.OperationalError:
    pass  # العمود موجود مسبقًا

# إنشاء جدول الأعمال إذا لم يكن موجود
c.execute('''
CREATE TABLE IF NOT EXISTS designs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    designer_id INTEGER,
    title TEXT,
    description TEXT,
    image_path TEXT
)
''')

# إنشاء جدول الطلبات إذا لم يكن موجود
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
print("تمت إضافة الأعمدة بنجاح (أو موجودة مسبقًا).")