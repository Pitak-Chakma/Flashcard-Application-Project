from app import app, db_adapter
from models import User, Card, Tag, CardReview, Achievement, UserAchievement, ActivityLog
import json

# Define the tables to be created in Supabase
tables = [
    {
        "name": "users",
        "columns": [
            {"name": "id", "type": "serial primary key"},
            {"name": "username", "type": "text not null unique"},
            {"name": "email", "type": "text not null unique"},
            {"name": "password", "type": "text not null"},
            {"name": "profile_pic", "type": "text default 'default_profile.png'"},
            {"name": "role", "type": "text default 'user'"},
            {"name": "date_joined", "type": "timestamp default now()"}
        ]
    },
    {
        "name": "cards",
        "columns": [
            {"name": "id", "type": "serial primary key"},
            {"name": "question", "type": "text not null"},
            {"name": "answer", "type": "text not null"},
            {"name": "date_created", "type": "timestamp default now()"},
            {"name": "is_public", "type": "boolean default false"},
            {"name": "user_id", "type": "integer references users(id) not null"}
        ]
    },
    {
        "name": "tags",
        "columns": [
            {"name": "id", "type": "serial primary key"},
            {"name": "name", "type": "text not null unique"}
        ]
    },
    {
        "name": "card_tags",
        "columns": [
            {"name": "card_id", "type": "integer references cards(id) not null"},
            {"name": "tag_id", "type": "integer references tags(id) not null"},
            {"name": "primary key", "type": "(card_id, tag_id)"}
        ]
    },
    {
        "name": "card_reviews",
        "columns": [
            {"name": "id", "type": "serial primary key"},
            {"name": "card_id", "type": "integer references cards(id) not null"},
            {"name": "user_id", "type": "integer references users(id) not null"},
            {"name": "ease_factor", "type": "float default 2.5"},
            {"name": "interval", "type": "integer default 1"},
            {"name": "next_review", "type": "timestamp"},
            {"name": "last_reviewed", "type": "timestamp default now()"}
        ]
    },
    {
        "name": "achievements",
        "columns": [
            {"name": "id", "type": "serial primary key"},
            {"name": "name", "type": "text not null"},
            {"name": "description", "type": "text not null"},
            {"name": "badge_image", "type": "text not null"}
        ]
    },
    {
        "name": "user_achievements",
        "columns": [
            {"name": "id", "type": "serial primary key"},
            {"name": "user_id", "type": "integer references users(id) not null"},
            {"name": "achievement_id", "type": "integer references achievements(id) not null"},
            {"name": "date_earned", "type": "timestamp default now()"}
        ]
    },
    {
        "name": "activity_logs",
        "columns": [
            {"name": "id", "type": "serial primary key"},
            {"name": "user_id", "type": "integer references users(id) not null"},
            {"name": "action", "type": "text not null"},
            {"name": "timestamp", "type": "timestamp default now()"},
            {"name": "details", "type": "text"}
        ]
    }
]

with app.app_context():
    print("Initializing Supabase tables...")
    
    # Generate SQL for creating tables
    sql_statements = []
    for table in tables:
        table_name = table["name"]
        print(f"Generating SQL for table: {table_name}")
        
        # Construct the CREATE TABLE SQL statement
        columns_sql = ", ".join([f"{col['name']} {col['type']}" for col in table["columns"]])
        create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_sql});"
        sql_statements.append(create_table_sql)
    
    # Print all SQL statements
    print("\n--- SQL Statements to Execute in Supabase SQL Editor ---")
    for sql in sql_statements:
        print(f"{sql}\n")
    
    print("\nIMPORTANT: This script generates the SQL needed to create tables.")
    print("To create these tables in Supabase:")
    print("1. Go to your Supabase project dashboard")
    print("2. Navigate to the SQL Editor")
    print("3. Create a new query and paste the generated SQL statements")
    print("4. Execute the SQL to create the tables")
    print("\nAlternatively, use Supabase's Table Editor to create these tables visually.")
    print("\nNote: Make sure your RLS (Row Level Security) policies are properly configured for each table.")
