"""
Supabase Service

This module provides a connection to Supabase and helper functions for
interacting with the Supabase database and storage.
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Supabase credentials from environment variables
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

class SupabaseService:
    """Service class for interacting with Supabase"""
    
    _instance = None
    _client = None
    
    @classmethod
    def get_instance(cls):
        """Singleton pattern to ensure only one instance of the service exists"""
        if cls._instance is None:
            cls._instance = SupabaseService()
        return cls._instance
    
    def __init__(self):
        """Initialize the Supabase client"""
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Supabase URL and Key must be set in environment variables")
        
        self._client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    @property
    def client(self) -> Client:
        """Get the Supabase client"""
        return self._client
    
    # User Management
    
    def get_user(self, user_id):
        """Get a user by ID"""
        return self._client.table('users').select('*').eq('id', user_id).execute()
    
    def create_user(self, user_data):
        """Create a new user"""
        return self._client.table('users').insert(user_data).execute()
    
    def update_user(self, user_id, user_data):
        """Update a user"""
        return self._client.table('users').update(user_data).eq('id', user_id).execute()
    
    def delete_user(self, user_id):
        """Delete a user"""
        return self._client.table('users').delete().eq('id', user_id).execute()
    
    # Card Management
    
    def get_cards(self, user_id=None, tag_id=None, is_public=None):
        """Get cards with optional filters"""
        query = self._client.table('cards').select('*')
        
        if user_id:
            query = query.eq('user_id', user_id)
        
        if tag_id:
            # This assumes a junction table for card_tags
            query = query.eq('tags.id', tag_id)
        
        if is_public is not None:
            query = query.eq('is_public', is_public)
            
        return query.execute()
    
    def get_card(self, card_id):
        """Get a card by ID"""
        return self._client.table('cards').select('*').eq('id', card_id).execute()
    
    def create_card(self, card_data):
        """Create a new card"""
        return self._client.table('cards').insert(card_data).execute()
    
    def update_card(self, card_id, card_data):
        """Update a card"""
        return self._client.table('cards').update(card_data).eq('id', card_id).execute()
    
    def delete_card(self, card_id):
        """Delete a card"""
        return self._client.table('cards').delete().eq('id', card_id).execute()
    
    # Card Review Management
    
    def get_due_reviews(self, user_id, limit=None):
        """Get reviews due for a user"""
        query = self._client.table('card_reviews') \
            .select('*') \
            .eq('user_id', user_id) \
            .lte('next_review', 'now()')
            
        if limit:
            query = query.limit(limit)
            
        return query.execute()
    
    def create_review(self, review_data):
        """Create a new review"""
        return self._client.table('card_reviews').insert(review_data).execute()
    
    def update_review(self, review_id, review_data):
        """Update a review"""
        return self._client.table('card_reviews').update(review_data).eq('id', review_id).execute()
    
    # Tag Management
    
    def get_tags(self):
        """Get all tags"""
        return self._client.table('tags').select('*').execute()
    
    def create_tag(self, tag_data):
        """Create a new tag"""
        return self._client.table('tags').insert(tag_data).execute()
    
    # Achievement Management
    
    def get_user_achievements(self, user_id):
        """Get achievements for a user"""
        return self._client.table('user_achievements').select('*').eq('user_id', user_id).execute()
    
    def award_achievement(self, user_id, achievement_id):
        """Award an achievement to a user"""
        achievement_data = {
            'user_id': user_id,
            'achievement_id': achievement_id,
            'date_earned': 'now()'
        }
        return self._client.table('user_achievements').insert(achievement_data).execute()
    
    # Activity Logging
    
    def log_activity(self, activity_data):
        """Log user activity"""
        return self._client.table('activity_logs').insert(activity_data).execute()
