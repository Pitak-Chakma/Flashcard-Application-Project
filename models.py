from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import enum

db = SQLAlchemy()

# Define user roles
class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

# Association table for card tags
card_tags = db.Table('card_tags',
    db.Column('card_id', db.Integer, db.ForeignKey('card.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
)

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    profile_pic = db.Column(db.String(100), default='default_profile.png')
    role = db.Column(db.Enum(UserRole), default=UserRole.USER)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    cards = db.relationship('Card', backref='author', lazy=True)
    achievements = db.relationship('UserAchievement', backref='user', lazy=True)
    
    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

# Card model  
class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    is_public = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    tags = db.relationship('Tag', secondary=card_tags, backref=db.backref('cards', lazy='dynamic'))
    reviews = db.relationship('CardReview', backref='card', lazy=True)
    
    def __repr__(self):
        return f"Card('{self.question[:30]}...', Created: '{self.date_created}')"

# Tag model
class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    
    def __repr__(self):
        return f"Tag('{self.name}')"

# Card review model for spaced repetition
class CardReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(db.Integer, db.ForeignKey('card.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ease_factor = db.Column(db.Float, default=2.5)
    interval = db.Column(db.Integer, default=1)  # in days
    next_review = db.Column(db.DateTime)
    last_reviewed = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"CardReview(Card: {self.card_id}, Next review: {self.next_review})"

# Achievement model
class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    badge_image = db.Column(db.String(100), nullable=False)
    
    # Relationship
    users = db.relationship('UserAchievement', backref='achievement', lazy=True)
    
    def __repr__(self):
        return f"Achievement('{self.name}')"

# User-Achievement association model
class UserAchievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievement.id'), nullable=False)
    date_earned = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"UserAchievement(User: {self.user_id}, Achievement: {self.achievement_id})"

# Activity log model for admin tracking
class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.Text)
    
    # Relationship
    user = db.relationship('User', backref='activities', lazy=True)
    
    def __repr__(self):
        return f"ActivityLog(User: {self.user_id}, Action: '{self.action[:30]}...', Time: {self.timestamp})"
