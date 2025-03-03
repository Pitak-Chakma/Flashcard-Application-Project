import os

class Config:
    # Secret key for session management
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'default-secret-key-change-in-production'
    
    # Database configuration
    DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flashcards.db')
    
    # Upload folder for any user uploads
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    
    # Application settings
    DEBUG = True
    TESTING = False
