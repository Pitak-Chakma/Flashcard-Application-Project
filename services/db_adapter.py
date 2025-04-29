"""
Database Adapter

This module provides an adapter pattern to switch between SQLite and Supabase
backends for data storage. This allows the application to use either backend
without changing the core application code.
"""

from flask import current_app
from models import db, User, Card, Tag, CardReview, Achievement, UserAchievement, ActivityLog
from services.supabase_service import SupabaseService
from datetime import datetime
import json

class DatabaseAdapter:
    """Adapter for database operations that can use either SQLite or Supabase"""
    
    def __init__(self, app=None):
        """Initialize the adapter with the current app"""
        self.app = app
        self._supabase = None
        
    @property
    def backend(self):
        """Get the current storage backend from config"""
        return current_app.config.get('STORAGE_BACKEND', 'sqlite')
    
    @property
    def supabase(self):
        """Get the Supabase service instance"""
        if self._supabase is None:
            self._supabase = SupabaseService.get_instance()
        return self._supabase
    
    # User operations
    
    def get_user(self, user_id):
        """Get a user by ID"""
        if self.backend == 'supabase':
            response = self.supabase.get_user(user_id)
            if response.data and len(response.data) > 0:
                return self._supabase_to_model(response.data[0], User)
        return User.query.get(user_id)
    
    def get_user_by_email(self, email):
        """Get a user by email"""
        if self.backend == 'supabase':
            response = self.supabase.client.table('users').select('*').eq('email', email).execute()
            if response.data and len(response.data) > 0:
                return self._supabase_to_model(response.data[0], User)
        return User.query.filter_by(email=email).first()
    
    def create_user(self, user_data):
        """Create a new user"""
        if self.backend == 'supabase':
            response = self.supabase.create_user(user_data)
            if response.data and len(response.data) > 0:
                return self._supabase_to_model(response.data[0], User)
        else:
            user = User(**user_data)
            db.session.add(user)
            db.session.commit()
            return user
    
    def update_user(self, user_id, user_data):
        """Update a user"""
        if self.backend == 'supabase':
            response = self.supabase.update_user(user_id, user_data)
            if response.data and len(response.data) > 0:
                return self._supabase_to_model(response.data[0], User)
        else:
            user = User.query.get(user_id)
            if user:
                for key, value in user_data.items():
                    setattr(user, key, value)
                db.session.commit()
                return user
    
    # Card operations
    
    def get_card(self, card_id):
        """Get a card by ID"""
        if self.backend == 'supabase':
            response = self.supabase.get_card(card_id)
            if response.data and len(response.data) > 0:
                return self._supabase_to_model(response.data[0], Card)
        return Card.query.get(card_id)
    
    def get_user_cards(self, user_id, tag_id=None):
        """Get cards for a user, optionally filtered by tag"""
        if self.backend == 'supabase':
            response = self.supabase.get_cards(user_id=user_id, tag_id=tag_id)
            if response.data:
                return [self._supabase_to_model(card_data, Card) for card_data in response.data]
        
        query = Card.query.filter_by(user_id=user_id)
        if tag_id:
            query = query.filter(Card.tags.any(id=tag_id))
        return query.all()
    
    def create_card(self, card_data, tags=None):
        """Create a new card with optional tags"""
        if self.backend == 'supabase':
            # Handle tags separately for Supabase
            tag_ids = card_data.pop('tag_ids', []) if tags is None else [tag.id for tag in tags]
            response = self.supabase.create_card(card_data)
            
            if response.data and len(response.data) > 0:
                card = self._supabase_to_model(response.data[0], Card)
                
                # Add tags to the card
                if tag_ids:
                    for tag_id in tag_ids:
                        self.supabase.client.table('card_tags').insert({
                            'card_id': card.id,
                            'tag_id': tag_id
                        }).execute()
                
                return card
        else:
            card = Card(**card_data)
            if tags:
                card.tags = tags
            db.session.add(card)
            db.session.commit()
            return card
    
    def update_card(self, card_id, card_data, tags=None):
        """Update a card with optional tags"""
        if self.backend == 'supabase':
            # Handle tags separately for Supabase
            tag_ids = card_data.pop('tag_ids', []) if tags is None else [tag.id for tag in tags]
            response = self.supabase.update_card(card_id, card_data)
            
            if response.data and len(response.data) > 0:
                card = self._supabase_to_model(response.data[0], Card)
                
                # Update tags (delete existing and add new)
                if tag_ids is not None:
                    # Delete existing tags
                    self.supabase.client.table('card_tags').delete().eq('card_id', card_id).execute()
                    
                    # Add new tags
                    for tag_id in tag_ids:
                        self.supabase.client.table('card_tags').insert({
                            'card_id': card.id,
                            'tag_id': tag_id
                        }).execute()
                
                return card
        else:
            card = Card.query.get(card_id)
            if card:
                for key, value in card_data.items():
                    setattr(card, key, value)
                if tags is not None:
                    card.tags = tags
                db.session.commit()
                return card
    
    def delete_card(self, card_id):
        """Delete a card"""
        if self.backend == 'supabase':
            # Delete card tags first
            self.supabase.client.table('card_tags').delete().eq('card_id', card_id).execute()
            # Delete card reviews
            self.supabase.client.table('card_reviews').delete().eq('card_id', card_id).execute()
            # Delete the card
            return self.supabase.delete_card(card_id)
        else:
            card = Card.query.get(card_id)
            if card:
                db.session.delete(card)
                db.session.commit()
                return True
    
    # Card Review operations
    
    def get_due_reviews(self, user_id, limit=None, tags=None):
        """Get reviews due for a user"""
        if self.backend == 'supabase':
            response = self.supabase.get_due_reviews(user_id, limit)
            if response.data:
                return [self._supabase_to_model(review_data, CardReview) for review_data in response.data]
        
        query = CardReview.query.filter(
            CardReview.user_id == user_id,
            CardReview.next_review <= datetime.utcnow()
        )
        
        if tags:
            query = query.join(Card).filter(Card.tags.any(Tag.id.in_(tags)))
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def get_review(self, review_id):
        """Get a review by ID"""
        if self.backend == 'supabase':
            response = self.supabase.client.table('card_reviews').select('*').eq('id', review_id).execute()
            if response.data and len(response.data) > 0:
                return self._supabase_to_model(response.data[0], CardReview)
        return CardReview.query.get(review_id)
    
    def create_review(self, review_data):
        """Create a new review"""
        if self.backend == 'supabase':
            response = self.supabase.create_review(review_data)
            if response.data and len(response.data) > 0:
                return self._supabase_to_model(response.data[0], CardReview)
        else:
            review = CardReview(**review_data)
            db.session.add(review)
            db.session.commit()
            return review
    
    def update_review(self, review_id, review_data):
        """Update a review"""
        if self.backend == 'supabase':
            response = self.supabase.update_review(review_id, review_data)
            if response.data and len(response.data) > 0:
                return self._supabase_to_model(response.data[0], CardReview)
        else:
            review = CardReview.query.get(review_id)
            if review:
                for key, value in review_data.items():
                    setattr(review, key, value)
                db.session.commit()
                return review
    
    # Tag operations
    
    def get_tags(self):
        """Get all tags"""
        if self.backend == 'supabase':
            response = self.supabase.get_tags()
            if response.data:
                return [self._supabase_to_model(tag_data, Tag) for tag_data in response.data]
        return Tag.query.all()
    
    def get_tag(self, tag_id):
        """Get a tag by ID"""
        if self.backend == 'supabase':
            response = self.supabase.client.table('tags').select('*').eq('id', tag_id).execute()
            if response.data and len(response.data) > 0:
                return self._supabase_to_model(response.data[0], Tag)
        return Tag.query.get(tag_id)
    
    def get_tag_by_name(self, name):
        """Get a tag by name"""
        if self.backend == 'supabase':
            response = self.supabase.client.table('tags').select('*').eq('name', name).execute()
            if response.data and len(response.data) > 0:
                return self._supabase_to_model(response.data[0], Tag)
        return Tag.query.filter_by(name=name).first()
    
    def create_tag(self, tag_data):
        """Create a new tag"""
        if self.backend == 'supabase':
            response = self.supabase.create_tag(tag_data)
            if response.data and len(response.data) > 0:
                return self._supabase_to_model(response.data[0], Tag)
        else:
            tag = Tag(**tag_data)
            db.session.add(tag)
            db.session.commit()
            return tag
    
    # Achievement operations
    
    def get_user_achievements(self, user_id):
        """Get achievements for a user"""
        if self.backend == 'supabase':
            response = self.supabase.get_user_achievements(user_id)
            if response.data:
                return [self._supabase_to_model(achievement_data, UserAchievement) for achievement_data in response.data]
        return UserAchievement.query.filter_by(user_id=user_id).all()
    
    def award_achievement(self, user_id, achievement_id):
        """Award an achievement to a user"""
        if self.backend == 'supabase':
            response = self.supabase.award_achievement(user_id, achievement_id)
            if response.data and len(response.data) > 0:
                return self._supabase_to_model(response.data[0], UserAchievement)
        else:
            user_achievement = UserAchievement(
                user_id=user_id,
                achievement_id=achievement_id,
                date_earned=datetime.utcnow()
            )
            db.session.add(user_achievement)
            db.session.commit()
            return user_achievement
    
    # Activity logging
    
    def log_activity(self, user_id, action, details=None):
        """Log user activity"""
        activity_data = {
            'user_id': user_id,
            'action': action,
            'details': details,
            'timestamp': datetime.utcnow().isoformat() if self.backend == 'supabase' else datetime.utcnow()
        }
        
        if self.backend == 'supabase':
            return self.supabase.log_activity(activity_data)
        else:
            log = ActivityLog(**activity_data)
            db.session.add(log)
            db.session.commit()
            return log
    
    # Helper methods
    
    def _supabase_to_model(self, data, model_class):
        """Convert Supabase data to SQLAlchemy model instance"""
        # Create a new instance of the model class
        instance = model_class()
        
        # Map Supabase data to model attributes
        for key, value in data.items():
            if hasattr(instance, key):
                # Handle datetime fields
                if isinstance(value, str) and key.endswith(('_at', '_date', 'date_', 'time', '_time', 'created', 'updated')):
                    try:
                        value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    except (ValueError, TypeError):
                        pass
                
                setattr(instance, key, value)
        
        return instance
