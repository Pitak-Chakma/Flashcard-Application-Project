import os

class Config:
    SECRET_KEY = 'your-secret-key'  # In production, use a secure random key
    SQLALCHEMY_DATABASE_URI = 'sqlite:///flashcards.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join('uploads', 'profile_pics')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
