"""
Spaced Repetition Service

This module implements an enhanced spaced repetition algorithm based on the SuperMemo SM-2 algorithm
with additional features for optimizing learning efficiency.
"""

from datetime import datetime, timedelta
import math
import random
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment variables (if needed for external services)
API_KEY = os.getenv('SPACED_REPETITION_API_KEY')

class SpacedRepetition:
    """
    Enhanced implementation of the SuperMemo SM-2 spaced repetition algorithm
    with additional features for optimizing learning efficiency.
    """
    
    # Difficulty ratings
    AGAIN = 1  # Complete failure to recall
    HARD = 2   # Significant difficulty recalling
    GOOD = 3   # Some difficulty but successful recall
    EASY = 4   # Perfect recall with no difficulty
    
    # Default parameters
    DEFAULT_EASE_FACTOR = 2.5
    MIN_EASE_FACTOR = 1.3
    MAX_EASE_FACTOR = 3.0
    
    @staticmethod
    def calculate_next_interval(current_interval, ease_factor, difficulty):
        """
        Calculate the next interval based on current interval, ease factor, and difficulty rating.
        
        Args:
            current_interval (int): Current interval in days
            ease_factor (float): Current ease factor
            difficulty (int): Difficulty rating (1-4)
            
        Returns:
            tuple: (new_interval, new_ease_factor)
        """
        # Ensure valid inputs
        current_interval = max(1, current_interval)
        ease_factor = max(SpacedRepetition.MIN_EASE_FACTOR, min(SpacedRepetition.MAX_EASE_FACTOR, ease_factor))
        
        # Calculate new ease factor based on performance
        if difficulty == SpacedRepetition.AGAIN:
            new_ease_factor = max(SpacedRepetition.MIN_EASE_FACTOR, ease_factor - 0.20)
            new_interval = 1  # Reset to 1 day for failed recall
        elif difficulty == SpacedRepetition.HARD:
            new_ease_factor = max(SpacedRepetition.MIN_EASE_FACTOR, ease_factor - 0.15)
            new_interval = max(1, int(current_interval * 1.2))
        elif difficulty == SpacedRepetition.GOOD:
            new_ease_factor = ease_factor  # No change
            new_interval = max(1, int(current_interval * ease_factor))
        elif difficulty == SpacedRepetition.EASY:
            new_ease_factor = min(SpacedRepetition.MAX_EASE_FACTOR, ease_factor + 0.15)
            new_interval = max(1, int(current_interval * ease_factor * 1.3))
        else:
            # Default to GOOD if invalid difficulty
            new_ease_factor = ease_factor
            new_interval = max(1, int(current_interval * ease_factor))
        
        # Add a small random factor to prevent cards from clustering
        randomization = random.uniform(0.95, 1.05)
        new_interval = max(1, int(new_interval * randomization))
        
        return new_interval, new_ease_factor
    
    @staticmethod
    def calculate_next_review_date(interval):
        """
        Calculate the next review date based on the interval.
        
        Args:
            interval (int): Interval in days
            
        Returns:
            datetime: Next review date
        """
        return datetime.utcnow() + timedelta(days=interval)
    
    @staticmethod
    def get_due_cards(user_id, card_model, review_model, session, limit=None, tags=None):
        """
        Get cards due for review, prioritized by urgency.
        
        Args:
            user_id (int): User ID
            card_model: Card model class
            review_model: CardReview model class
            session: Database session
            limit (int, optional): Maximum number of cards to return
            tags (list, optional): List of tag IDs to filter by
            
        Returns:
            list: List of card reviews due for review
        """
        query = session.query(review_model).filter(
            review_model.user_id == user_id,
            review_model.next_review <= datetime.utcnow()
        )
        
        # If tags are specified, filter by tags
        if tags and len(tags) > 0:
            query = query.join(card_model).filter(
                card_model.tags.any(id.in_(tags))
            )
        
        # Order by urgency (overdue cards first)
        query = query.order_by(review_model.next_review.asc())
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    @staticmethod
    def get_learning_efficiency(user_id, review_model, session, days=30):
        """
        Calculate learning efficiency based on review history.
        
        Args:
            user_id (int): User ID
            review_model: CardReview model class
            session: Database session
            days (int): Number of days to analyze
            
        Returns:
            dict: Learning efficiency metrics
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get all reviews in the time period
        reviews = session.query(review_model).filter(
            review_model.user_id == user_id,
            review_model.last_reviewed >= start_date
        ).all()
        
        if not reviews:
            return {
                "total_reviews": 0,
                "average_ease": 0,
                "retention_rate": 0,
                "review_streak": 0
            }
        
        # Calculate metrics
        total_reviews = len(reviews)
        average_ease = sum(r.ease_factor for r in reviews) / total_reviews
        
        # Calculate retention rate (percentage of non-failed reviews)
        successful_reviews = sum(1 for r in reviews if r.interval > 1)
        retention_rate = (successful_reviews / total_reviews) * 100 if total_reviews > 0 else 0
        
        # Calculate current streak
        # Group reviews by day
        review_days = set()
        for review in reviews:
            review_days.add(review.last_reviewed.date())
        
        # Count consecutive days up to today
        streak = 0
        today = datetime.utcnow().date()
        for i in range(days):
            check_date = today - timedelta(days=i)
            if check_date in review_days:
                streak += 1
            else:
                break
        
        return {
            "total_reviews": total_reviews,
            "average_ease": round(average_ease, 2),
            "retention_rate": round(retention_rate, 2),
            "review_streak": streak
        }
