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
from flask import current_app
from services.db_adapter import DatabaseAdapter

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
    def safe_parse_datetime(datetime_str):
        """
        Safely parse a datetime string in various formats.
        
        Args:
            datetime_str (str): Datetime string to parse
            
        Returns:
            datetime: Parsed datetime object or None if parsing fails
        """
        if not isinstance(datetime_str, str):
            return datetime_str  # Already a datetime object or None
            
        try:
            # Try standard parsing first
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except ValueError:
            try:
                # Try with regex to extract components
                import re
                
                # Extract date and time parts
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', datetime_str)
                time_match = re.search(r'(\d{2}:\d{2}:\d{2})(\.\d+)?', datetime_str)
                
                if date_match and time_match:
                    date_part = date_match.group(1)
                    time_part = time_match.group(1)
                    microseconds = time_match.group(2) if time_match.group(2) else ''
                    
                    # Format microseconds properly if present
                    if microseconds:
                        # Remove the dot and pad/truncate to 6 digits
                        microseconds = microseconds[1:].ljust(6, '0')[:6]
                        time_part = f"{time_part}.{microseconds}"
                    
                    # Create a properly formatted datetime string
                    formatted_value = f"{date_part} {time_part}"
                    return datetime.strptime(formatted_value, '%Y-%m-%d %H:%M:%S.%f' if microseconds else '%Y-%m-%d %H:%M:%S')
                else:
                    # If regex fails, try simple date format
                    return datetime.strptime(datetime_str.split('T')[0], '%Y-%m-%d')
            except Exception as e:
                # If all parsing attempts fail, log and return current time
                current_app.logger.error(f"Error parsing datetime '{datetime_str}': {str(e)}")
                return datetime.utcnow()
    
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
    def get_due_cards(user_id, limit=None, tags=None):
        """
        Get cards due for review, prioritized by urgency.
        
        Args:
            user_id (int): User ID
            limit (int, optional): Maximum number of cards to return
            tags (list, optional): List of tag IDs to filter by
            
        Returns:
            list: List of card reviews due for review
        """
        # Get database adapter
        db_adapter = DatabaseAdapter()
        
        # Use the adapter to get due reviews
        return db_adapter.get_due_reviews(user_id, limit=limit, tags=tags)
    
    @staticmethod
    def get_learning_efficiency(user_id, days=30):
        """
        Calculate learning efficiency based on review history.
        
        Args:
            user_id (int): User ID
            days (int): Number of days to analyze
            
        Returns:
            dict: Learning efficiency metrics
        """
        # Get database adapter
        db_adapter = DatabaseAdapter()
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get all reviews in the time period using the adapter
        if db_adapter.backend == 'supabase':
            # For Supabase, use the client directly
            response = db_adapter.supabase.client.table('card_reviews').select('*').eq('user_id', user_id).gte('last_reviewed', start_date.isoformat()).execute()
            reviews = response.data if response.data else []
        else:
            # For SQLite, use the model
            from models import CardReview
            reviews = CardReview.query.filter(
                CardReview.user_id == user_id,
                CardReview.last_reviewed >= start_date
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
        
        # Handle both SQLAlchemy model and dict from Supabase
        def get_attr(review, attr):
            return review[attr] if isinstance(review, dict) else getattr(review, attr)
        
        average_ease = sum(get_attr(r, 'ease_factor') for r in reviews) / total_reviews
        
        # Calculate retention rate (percentage of non-failed reviews)
        successful_reviews = sum(1 for r in reviews if get_attr(r, 'interval') > 1)
        retention_rate = (successful_reviews / total_reviews) * 100 if total_reviews > 0 else 0
        
        # Calculate current streak
        # Group reviews by day
        review_days = set()
        for review in reviews:
            try:
                # Handle datetime format from both SQLAlchemy and Supabase
                last_reviewed = get_attr(review, 'last_reviewed')
                
                # For SQLAlchemy objects (already datetime objects)
                if hasattr(last_reviewed, 'date'):
                    review_days.add(last_reviewed.date())
                # For string dates from Supabase
                elif isinstance(last_reviewed, str):
                    # Just extract the date part (YYYY-MM-DD) without parsing the full datetime
                    date_str = last_reviewed.split('T')[0] if 'T' in last_reviewed else last_reviewed.split(' ')[0]
                    year, month, day = map(int, date_str.split('-'))
                    review_days.add(datetime(year, month, day).date())
                else:
                    # Fallback to today's date
                    current_app.logger.warning(f"Unknown date format: {last_reviewed}")
                    review_days.add(datetime.utcnow().date())
            except Exception as e:
                current_app.logger.error(f"Error processing review date: {str(e)}")
                # Fallback to today's date
                review_days.add(datetime.utcnow().date())
        
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
