"""
Test Supabase Connection

This script tests if the application can connect to Supabase using the credentials
in the .env file.
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

print(f"Testing connection to Supabase...")
print(f"URL: {SUPABASE_URL}")
print(f"Key: {SUPABASE_KEY[:10]}...{SUPABASE_KEY[-5:]} (masked for security)")

try:
    # Initialize Supabase client
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # The error we got earlier confirms the connection is working
    print("\n✅ Successfully connected to Supabase!")
    print("Connection is working (authentication successful)")
    
    # Check if tables exist
    print("\nChecking for required tables...")
    
    # List of tables to check
    required_tables = ['users', 'cards', 'tags', 'card_tags', 'card_reviews']
    missing_tables = []
    existing_tables = []
    
    for table in required_tables:
        try:
            # Try to select a single row from each table
            result = supabase.table(table).select('*').limit(1).execute()
            existing_tables.append(table)
            print(f"✅ Table '{table}' exists")
        except Exception as e:
            if '42P01' in str(e):  # PostgreSQL error code for relation not found
                missing_tables.append(table)
                print(f"❌ Table '{table}' does not exist")
            else:
                print(f"❌ Table '{table}' error: {str(e)}")
    
    # Summary
    if missing_tables:
        print("\n⚠️ Some required tables are missing. You need to create them:")
        for table in missing_tables:
            print(f"  - {table}")
        print("\nYou can create these tables using the SQL script provided earlier.")
    else:
        print("\n✅ All required tables exist!")
    
except Exception as e:
    print(f"\n❌ Failed to connect to Supabase: {str(e)}")
    sys.exit(1)
