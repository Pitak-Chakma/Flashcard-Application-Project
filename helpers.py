import datetime
import random
import string
from functools import wraps
from flask import session, redirect, url_for, flash, g

# Authentication helper
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Calculate spaced repetition interval based on performance
def calculate_next_review(review_count, is_correct):
    """
    Calculate when the next review should occur based on performance
    Using a modified version of the SM-2 algorithm
    """
    if is_correct:
        # If correct, increase interval exponentially
        # 1 day, 3 days, 7 days, 14 days, 30 days, etc.
        intervals = [1, 3, 7, 14, 30, 60, 120]
        if review_count <= len(intervals):
            days = intervals[review_count - 1]
        else:
            days = intervals[-1]
    else:
        # If incorrect, reset to a short interval (12 hours)
        days = 0.5
    
    now = datetime.datetime.now()
    next_review = now + datetime.timedelta(days=days)
    return next_review

# Generate a random ID (for various purposes)
def generate_id(length=8):
    """Generate a random alphanumeric ID"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

# Format datetime objects for display
def format_datetime(dt, format='%B %d, %Y at %H:%M'):
    """Format a datetime object as a readable string"""
    if isinstance(dt, str):
        try:
            dt = datetime.datetime.fromisoformat(dt)
        except ValueError:
            return dt
    return dt.strftime(format)

# Calculate progress statistics
def calculate_success_rate(correct, total):
    """Calculate success rate as a percentage"""
    if total == 0:
        return 0
    return round((correct / total) * 100, 1)

# Check if a user has earned a new achievement
def check_achievements(user_id, stats):
    """Check if a user has earned any new achievements based on stats"""
    from models import Reward
    
    achievements = []
    
    # Achievement: First 10 flashcards created
    if stats['total_cards'] >= 10:
        achievements.append({
            'name': 'Flashcard Creator',
            'description': 'Created 10 or more flashcards'
        })
    
    # Achievement: First 50 flashcards created
    if stats['total_cards'] >= 50:
        achievements.append({
            'name': 'Flashcard Master',
            'description': 'Created 50 or more flashcards'
        })
    
    # Achievement: 100 review sessions
    if stats['total_attempts'] >= 100:
        achievements.append({
            'name': 'Dedicated Learner',
            'description': 'Completed 100 review sessions'
        })
    
    # Achievement: 85% success rate (after at least 20 attempts)
    if stats['total_attempts'] >= 20 and stats['success_rate'] >= 85:
        achievements.append({
            'name': 'Memory Champion',
            'description': 'Maintained at least 85% success rate after 20+ reviews'
        })
    
    # Grant new achievements to the user
    for achievement in achievements:
        Reward.grant(user_id, achievement['name'], achievement['description'])
    
    return achievements
