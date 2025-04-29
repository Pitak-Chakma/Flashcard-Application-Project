import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Use environment variables with fallbacks for sensitive information
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///flashcards.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join('uploads', 'profile_pics')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    
    # Spaced repetition settings
    SPACED_REPETITION_API_KEY = os.getenv('SPACED_REPETITION_API_KEY')
    # Maximum number of cards to review per session
    MAX_CARDS_PER_SESSION = int(os.getenv('MAX_CARDS_PER_SESSION', '20'))
    
    # Supabase configuration
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    
    # Storage backend ('sqlite' or 'supabase')
    STORAGE_BACKEND = os.getenv('STORAGE_BACKEND', 'sqlite')
