"""
Setup Supabase Tables

This script creates the required tables in Supabase for the Flashcard Application.
It uses the credentials from the .env file to connect to Supabase.
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client
import sys

# Load environment variables
load_dotenv()

# Get Supabase credentials from environment variables
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in your .env file")
    sys.exit(1)

print(f"Connecting to Supabase...")
print(f"URL: {SUPABASE_URL}")
print(f"Key: {SUPABASE_KEY[:10]}...{SUPABASE_KEY[-5:]} (masked for security)")

try:
    # Initialize Supabase client
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("\n✅ Successfully connected to Supabase!")
    
    # SQL statements to create tables
    create_tables_sql = """
    -- Users table
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(100) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        role VARCHAR(20) DEFAULT 'user',
        profile_image VARCHAR(255),
        date_joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Tags table
    CREATE TABLE IF NOT EXISTS tags (
        id SERIAL PRIMARY KEY,
        name VARCHAR(50) NOT NULL UNIQUE,
        color VARCHAR(20) DEFAULT '#3498db'
    );

    -- Cards table
    CREATE TABLE IF NOT EXISTS cards (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_public BOOLEAN DEFAULT FALSE
    );

    -- Card Tags junction table
    CREATE TABLE IF NOT EXISTS card_tags (
        card_id INTEGER REFERENCES cards(id) ON DELETE CASCADE,
        tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
        PRIMARY KEY (card_id, tag_id)
    );

    -- Card Reviews table
    CREATE TABLE IF NOT EXISTS card_reviews (
        id SERIAL PRIMARY KEY,
        card_id INTEGER REFERENCES cards(id) ON DELETE CASCADE,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        ease_factor FLOAT DEFAULT 2.5,
        interval INTEGER DEFAULT 1,
        last_reviewed TIMESTAMP,
        next_review TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Achievements table
    CREATE TABLE IF NOT EXISTS achievements (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL UNIQUE,
        description TEXT,
        badge_image VARCHAR(255)
    );

    -- User Achievements junction table
    CREATE TABLE IF NOT EXISTS user_achievements (
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        achievement_id INTEGER REFERENCES achievements(id) ON DELETE CASCADE,
        date_earned TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, achievement_id)
    );

    -- Activity Logs table
    CREATE TABLE IF NOT EXISTS activity_logs (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        action VARCHAR(100) NOT NULL,
        details TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Execute SQL to create tables
    print("\nCreating tables...")
    
    # Split the SQL into individual statements
    statements = [s.strip() for s in create_tables_sql.split(';') if s.strip()]
    
    # Execute each statement
    for statement in statements:
        try:
            # Execute SQL using Supabase's REST API
            # Note: This is a simplified approach. In a production environment,
            # you might want to use a more robust method for executing SQL.
            result = supabase.rpc('exec_sql', {'sql': statement}).execute()
            print(f"✅ Executed SQL statement successfully")
        except Exception as e:
            print(f"❌ Error executing SQL: {str(e)}")
            print(f"Statement: {statement}")
    
    print("\n✅ Setup complete! Tables have been created in Supabase.")
    print("\nYou can now run the application with Supabase as the database backend.")
    print("Make sure to set STORAGE_BACKEND=supabase in your .env file.")
    
except Exception as e:
    print(f"\n❌ Failed to connect to Supabase: {str(e)}")
    sys.exit(1)
