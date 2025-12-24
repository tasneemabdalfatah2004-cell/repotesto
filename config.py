import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = 'super-secret-key'
    DATABASE = os.path.join(BASE_DIR, 'database/db.sqlite')
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app/static/uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}