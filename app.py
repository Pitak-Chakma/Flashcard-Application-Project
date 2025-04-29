from flask import Flask, render_template, url_for, flash, redirect, request, abort, jsonify
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
import random
from config import Config
from models import db, User, UserRole, Card, Tag, CardReview, Achievement, UserAchievement, ActivityLog
from forms import (RegistrationForm, LoginForm, UpdateProfileForm, CreateCardForm, 
                  SearchCardForm, ChangePasswordForm)
from sqlalchemy import func
from services.spaced_repetition import SpacedRepetition
from services.db_adapter import DatabaseAdapter

# Initialize the app
app = Flask(__name__)
app.config.from_object(Config)

# Set up the database
db.init_app(app)

# Initialize database adapter
db_adapter = DatabaseAdapter(app)

# Set up login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create folders if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Helper function to log activity
def log_activity(user_id, action, details=None):
    with app.app_context():
        db_adapter.log_activity(user_id, action, details)

# Home page route
@app.route('/')
def index():
    return render_template('index.html')

# User registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        
        # Add to database
        db.session.add(user)
        db.session.commit()
        
        # Log activity
        log_activity(user.id, "User registered")
        
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

# User login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            log_activity(user.id, "User logged in")
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')
    
    return render_template('login.html', form=form)

# User logout route
@app.route('/logout')
@login_required
def logout():
    log_activity(current_user.id, "User logged out")
    logout_user()
    return redirect(url_for('index'))

# User dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    # Get user stats
    user_cards = Card.query.filter_by(user_id=current_user.id).count()
    reviews_today = CardReview.query.filter(
        CardReview.user_id == current_user.id,
        CardReview.next_review <= datetime.utcnow()
    ).count()
    achievements = UserAchievement.query.filter_by(user_id=current_user.id).all()
    
    # Check for admin
    is_admin = current_user.role == UserRole.ADMIN
    
    return render_template('dashboard.html', 
                          user_cards=user_cards, 
                          reviews_today=reviews_today,
                          achievements=achievements,
                          is_admin=is_admin)

# User profile
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateProfileForm()
    
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        
        # Handle profile pic upload
        if form.profile_pic.data:
            picture_file = save_profile_picture(form.profile_pic.data)
            current_user.profile_pic = picture_file
        
        db.session.commit()
        log_activity(current_user.id, "Profile updated")
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('profile'))
    
    # Pre-populate the form
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    
    return render_template('profile.html', form=form)

# Helper function to save profile pictures
def save_profile_picture(form_picture):
    # Generate a random filename to avoid collisions
    random_hex = os.urandom(8).hex()
    _, f_ext = os.path.splitext(secure_filename(form_picture.filename))
    picture_filename = random_hex + f_ext
    
    picture_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], picture_filename)
    form_picture.save(picture_path)
    
    return picture_filename

# Change password
@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if check_password_hash(current_user.password, form.current_password.data):
            hashed_password = generate_password_hash(form.new_password.data)
            current_user.password = hashed_password
            db.session.commit()
            log_activity(current_user.id, "Password changed")
            flash('Your password has been updated!', 'success')
            return redirect(url_for('profile'))
        else:
            flash('Current password is incorrect.', 'danger')
    
    return render_template('change_password.html', form=form)

# Delete account
@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    # Delete all user's cards, reviews, and achievements first
    Card.query.filter_by(user_id=current_user.id).delete()
    CardReview.query.filter_by(user_id=current_user.id).delete()
    UserAchievement.query.filter_by(user_id=current_user.id).delete()
    ActivityLog.query.filter_by(user_id=current_user.id).delete()
    
    # Delete the user
    user_id = current_user.id
    db.session.delete(current_user)
    db.session.commit()
    
    flash('Your account has been deleted.', 'info')
    return redirect(url_for('index'))

# Create flashcard
@app.route('/create_card', methods=['GET', 'POST'])
@login_required
def create_card():
    form = CreateCardForm()
    
    if form.validate_on_submit():
        # Create the card
        card = Card(
            question=form.question.data,
            answer=form.answer.data,
            is_public=form.is_public.data,
            user_id=current_user.id
        )
        
        # Process tags
        if form.tags.data:
            tag_names = [tag.strip() for tag in form.tags.data.split(',')]
            for tag_name in tag_names:
                # Check if tag exists, create if it doesn't
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                card.tags.append(tag)
        
        # Add card to database
        db.session.add(card)
        db.session.commit()
        
        # Create initial review interval
        review = CardReview(
            card_id=card.id,
            user_id=current_user.id,
            next_review=datetime.utcnow()
        )
        db.session.add(review)
        db.session.commit()
        
        log_activity(current_user.id, "Created flashcard", f"Card ID: {card.id}")
        flash('Your flashcard has been created!', 'success')
        return redirect(url_for('view_cards'))
    
    return render_template('create_card.html', form=form)

# View flashcards
@app.route('/view_cards')
@login_required
def view_cards():
    search_form = SearchCardForm()
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    tag_filter = request.args.get('tag', '')
    
    # Base query: user's own cards
    query = Card.query.filter_by(user_id=current_user.id)
    
    # Apply search if provided
    if search:
        query = query.filter(
            (Card.question.contains(search)) | 
            (Card.answer.contains(search))
        )
    
    # Apply tag filter if provided
    if tag_filter:
        tag = Tag.query.filter_by(name=tag_filter).first()
        if tag:
            query = query.filter(Card.tags.contains(tag))
    
    # Get paginated results
    cards = query.order_by(Card.date_created.desc()).paginate(page=page, per_page=10)
    
    # Get all tags for filter dropdown
    all_tags = Tag.query.join(Tag.cards).filter(Card.user_id == current_user.id).distinct().all()
    
    return render_template('view_cards.html', cards=cards, search_form=search_form, 
                          all_tags=all_tags, current_search=search, current_tag=tag_filter)

# Edit flashcard
@app.route('/edit_card/<int:card_id>', methods=['GET', 'POST'])
@login_required
def edit_card(card_id):
    card = Card.query.get_or_404(card_id)
    
    # Check if user owns the card
    if card.user_id != current_user.id:
        abort(403)  # Forbidden
    
    form = CreateCardForm()
    
    if form.validate_on_submit():
        card.question = form.question.data
        card.answer = form.answer.data
        card.is_public = form.is_public.data
        
        # Update tags
        card.tags.clear()
        if form.tags.data:
            tag_names = [tag.strip() for tag in form.tags.data.split(',')]
            for tag_name in tag_names:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                card.tags.append(tag)
        
        db.session.commit()
        log_activity(current_user.id, "Edited flashcard", f"Card ID: {card.id}")
        flash('Your flashcard has been updated!', 'success')
        return redirect(url_for('view_cards'))
    
    # Pre-populate the form
    elif request.method == 'GET':
        form.question.data = card.question
        form.answer.data = card.answer
        form.is_public.data = card.is_public
        form.tags.data = ', '.join([tag.name for tag in card.tags])
    
    return render_template('create_card.html', form=form, title='Edit Flashcard')

# Delete flashcard
@app.route('/delete_card/<int:card_id>', methods=['POST'])
@login_required
def delete_card(card_id):
    card = Card.query.get_or_404(card_id)
    
    # Check if user owns the card
    if card.user_id != current_user.id:
        abort(403)  # Forbidden
    
    # Delete related reviews
    CardReview.query.filter_by(card_id=card.id).delete()
    
    # Delete the card
    db.session.delete(card)
    db.session.commit()
    
    log_activity(current_user.id, "Deleted flashcard", f"Card ID: {card.id}")
    flash('Your flashcard has been deleted!', 'success')
    return redirect(url_for('view_cards'))

# Study route
@app.route('/study')
@login_required
def study():
    # Count cards due for review
    due_count = CardReview.query.filter(
        CardReview.user_id == current_user.id,
        CardReview.next_review <= datetime.utcnow()
    ).count()
    
    # Count cards without reviews (new cards)
    new_count = Card.query.filter(
        Card.user_id == current_user.id,
        ~Card.id.in_(db.session.query(CardReview.card_id).filter_by(user_id=current_user.id))
    ).count()
    
    # Get all tags for filtering
    tags = Tag.query.all()
    
    # Get learning efficiency metrics
    efficiency = SpacedRepetition.get_learning_efficiency(
        user_id=current_user.id,
        review_model=CardReview,
        session=db.session
    )
    
    return render_template('study.html', 
                          due_count=due_count, 
                          new_count=new_count,
                          tags=tags,
                          efficiency=efficiency)

# API to get next card for study
@app.route('/api/get_next_card')
@login_required
def get_next_card():
    # Get tag filter if provided
    tag_ids = request.args.getlist('tags', type=int)
    
    # Use the database adapter to get due reviews
    reviews = db_adapter.get_due_reviews(
        user_id=current_user.id,
        limit=1,
        tags=tag_ids if tag_ids else None
    )
    
    if not reviews:
        # Check if there are any cards without reviews yet
        # For SQLite, we'll use the existing query
        # For Supabase, we'll use a custom query through the adapter
        if app.config['STORAGE_BACKEND'] == 'sqlite':
            cards_without_reviews = Card.query.filter(
                Card.user_id == current_user.id,
                ~Card.id.in_(db.session.query(CardReview.card_id).filter_by(user_id=current_user.id))
            )
            
            # Apply tag filter if provided
            if tag_ids:
                cards_without_reviews = cards_without_reviews.filter(
                    Card.tags.any(Tag.id.in_(tag_ids))
                )
                
            card = cards_without_reviews.first()
        else:
            # For Supabase, we'll use a custom query through the adapter
            # This would need to be implemented in the adapter
            # For now, we'll just get all user cards and filter in Python
            all_user_cards = db_adapter.get_user_cards(current_user.id, tag_id=tag_ids[0] if tag_ids else None)
            all_reviews = db_adapter.supabase.client.table('card_reviews').select('card_id').eq('user_id', current_user.id).execute()
            reviewed_card_ids = [r['card_id'] for r in all_reviews.data] if all_reviews.data else []
            
            # Filter cards that don't have reviews
            cards_without_reviews = [c for c in all_user_cards if c.id not in reviewed_card_ids]
            card = cards_without_reviews[0] if cards_without_reviews else None
        
        if card:
            # Create a new review for this card
            review_data = {
                'card_id': card.id,
                'user_id': current_user.id,
                'ease_factor': SpacedRepetition.DEFAULT_EASE_FACTOR,
                'interval': 1,
                'next_review': datetime.utcnow()
            }
            
            review = db_adapter.create_review(review_data)
            
            # Get tags for the card
            if app.config['STORAGE_BACKEND'] == 'sqlite':
                tags = [tag.name for tag in card.tags]
            else:
                # For Supabase, we need to get tags separately
                tag_response = db_adapter.supabase.client.table('card_tags')\
                    .select('tags(name)')\
                    .eq('card_id', card.id)\
                    .execute()
                
                tags = [item['tags']['name'] for item in tag_response.data] if tag_response.data else []
            
            return jsonify({
                'status': 'success',
                'card_id': card.id,
                'question': card.question,
                'answer': card.answer,
                'tags': tags,
                'review_id': review.id,
                'new_card': True
            })
        else:
            return jsonify({'status': 'complete'})
    
    # Get the first review (most urgent)
    review = reviews[0]
    card = db_adapter.get_card(review.card_id)
    
    # Get tags for the card
    if app.config['STORAGE_BACKEND'] == 'sqlite':
        tags = [tag.name for tag in card.tags]
    else:
        # For Supabase, we need to get tags separately
        tag_response = db_adapter.supabase.client.table('card_tags')\
            .select('tags(name)')\
            .eq('card_id', card.id)\
            .execute()
        
        tags = [item['tags']['name'] for item in tag_response.data] if tag_response.data else []
    
    return jsonify({
        'status': 'success',
        'card_id': card.id,
        'question': card.question,
        'answer': card.answer,
        'tags': tags,
        'review_id': review.id,
        'new_card': False,
        'current_interval': review.interval,
        'ease_factor': round(review.ease_factor, 2)
    })

# API to update card review based on difficulty
@app.route('/api/update_review/<int:review_id>', methods=['POST'])
@login_required
def update_review(review_id):
    # Get the review using the database adapter
    review = db_adapter.get_review(review_id)
    if not review:
        abort(404)
    
    # Check if user owns the review
    if review.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    # Get difficulty rating from request (1-4 scale)
    data = request.get_json()
    difficulty = int(data.get('difficulty', 3))
    
    # Use the spaced repetition service to calculate the next interval and ease factor
    new_interval, new_ease_factor = SpacedRepetition.calculate_next_interval(
        current_interval=review.interval,
        ease_factor=review.ease_factor,
        difficulty=difficulty
    )
    
    # Prepare the updated review data
    next_review_date = SpacedRepetition.calculate_next_review_date(new_interval)
    review_data = {
        'interval': new_interval,
        'ease_factor': new_ease_factor,
        'last_reviewed': datetime.utcnow(),
        'next_review': next_review_date
    }
    
    # Update the review using the database adapter
    updated_review = db_adapter.update_review(review_id, review_data)
    
    log_activity(current_user.id, "Reviewed flashcard", 
                f"Card ID: {review.card_id}, Difficulty: {difficulty}, Next review in {new_interval} days")
    
    # Check for achievements
    check_review_achievements(current_user.id)
    
    # Get learning efficiency metrics
    if app.config['STORAGE_BACKEND'] == 'sqlite':
        efficiency = SpacedRepetition.get_learning_efficiency(
            user_id=current_user.id,
            review_model=CardReview,
            session=db.session
        )
    else:
        # For Supabase, we need to calculate efficiency differently
        # This is a simplified version for now
        reviews_response = db_adapter.supabase.client.table('card_reviews')\
            .select('*')\
            .eq('user_id', current_user.id)\
            .gte('last_reviewed', (datetime.utcnow() - timedelta(days=30)).isoformat())\
            .execute()
        
        reviews = reviews_response.data if reviews_response.data else []
        
        if not reviews:
            efficiency = {
                "total_reviews": 0,
                "average_ease": 0,
                "retention_rate": 0,
                "review_streak": 0
            }
        else:
            total_reviews = len(reviews)
            average_ease = sum(r['ease_factor'] for r in reviews) / total_reviews
            successful_reviews = sum(1 for r in reviews if r['interval'] > 1)
            retention_rate = (successful_reviews / total_reviews) * 100 if total_reviews > 0 else 0
            
            # Calculate streak (simplified)
            review_days = set()
            for review in reviews:
                review_date = datetime.fromisoformat(review['last_reviewed'].replace('Z', '+00:00')).date()
                review_days.add(review_date)
            
            streak = 0
            today = datetime.utcnow().date()
            for i in range(30):  # Check last 30 days
                check_date = today - timedelta(days=i)
                if check_date in review_days:
                    streak += 1
                else:
                    break
            
            efficiency = {
                "total_reviews": total_reviews,
                "average_ease": round(average_ease, 2),
                "retention_rate": round(retention_rate, 2),
                "review_streak": streak
            }
    
    return jsonify({
        'status': 'success',
        'new_interval': new_interval,
        'new_ease_factor': round(new_ease_factor, 2),
        'next_review': next_review_date.strftime('%Y-%m-%d'),
        'efficiency': efficiency
    })

# Helper function to check and award review-based achievements
def check_review_achievements(user_id):
    # Count total reviews
    review_count = CardReview.query.filter(
        CardReview.user_id == user_id,
        CardReview.last_reviewed != None
    ).count()
    
    # Milestone achievements
    milestones = {
        10: "Beginner Reviewer",
        50: "Intermediate Reviewer", 
        100: "Advanced Reviewer",
        500: "Master Reviewer"
    }
    
    for count, name in milestones.items():
        if review_count >= count:
            # Check if user already has this achievement
            achievement = Achievement.query.filter_by(name=name).first()
            
            if not achievement:
                # Create achievement if it doesn't exist
                achievement = Achievement(
                    name=name,
                    description=f"Completed {count} flashcard reviews",
                    badge_image=f"badge_{count}.png"
                )
                db.session.add(achievement)
                db.session.flush()
            
            # Check if user already has this achievement
            user_achievement = UserAchievement.query.filter_by(
                user_id=user_id,
                achievement_id=achievement.id
            ).first()
            
            if not user_achievement:
                # Award achievement
                new_achievement = UserAchievement(
                    user_id=user_id,
                    achievement_id=achievement.id
                )
                db.session.add(new_achievement)
                db.session.commit()
                
                log_activity(user_id, "Earned achievement", f"Achievement: {name}")

# Admin dashboard
@app.route('/admin')
@login_required
def admin_dashboard():
    # Check if user is admin
    if current_user.role != UserRole.ADMIN:
        abort(403)  # Forbidden
    
    # Get stats for admin dashboard
    total_users = User.query.count()
    total_cards = Card.query.count()
    total_reviews = CardReview.query.count()
    
    # Get recent activity logs
    activity_logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(50).all()
    
    # Get user list
    users = User.query.all()
    
    return render_template('admin.html', total_users=total_users, total_cards=total_cards,
                          total_reviews=total_reviews, activity_logs=activity_logs,
                          users=users)

# Admin: edit user
@app.route('/admin/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_user(user_id):
    # Check if user is admin
    if current_user.role != UserRole.ADMIN:
        abort(403)  # Forbidden
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        user.role = UserRole(request.form.get('role'))
        
        db.session.commit()
        log_activity(current_user.id, "Admin edited user", f"User ID: {user.id}")
        flash('User has been updated!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin_edit_user.html', user=user, roles=UserRole)

# Initialize database
@app.before_first_request
def create_tables():
    db.create_all()
    
    # Create admin user if not exists
    admin = User.query.filter_by(email='admin@example.com').first()
    if not admin:
        hashed_password = generate_password_hash('admin123')
        admin = User(username='admin', email='admin@example.com', 
                    password=hashed_password, role=UserRole.ADMIN)
        db.session.add(admin)
        db.session.commit()

@app.route('/api/study_progress/data')
@login_required
def get_study_progress_data():
    try:
        # Get reviews for the past 7 days
        end_date = datetime.now().replace(hour=23, minute=59, second=59)
        start_date = (end_date - timedelta(days=6)).replace(hour=0, minute=0, second=0)
        
        # Query reviews within date range
        reviews = db.session.query(
            func.date(CardReview.last_reviewed).label('review_date'),
            func.count().label('count')
        ).filter(
            CardReview.user_id == current_user.id,
            CardReview.last_reviewed >= start_date,
            CardReview.last_reviewed <= end_date,
            CardReview.last_reviewed != None  # Make sure we only count reviews that happened
        ).group_by(func.date(CardReview.last_reviewed)).all()
        
        # Convert to dictionary for easy lookup
        review_counts = {r.review_date.strftime('%Y-%m-%d'): r.count for r in reviews}
        
        # Prepare data for the past 7 days
        labels = []
        data = []
        
        for i in range(6, -1, -1):
            day = (end_date - timedelta(days=i)).date()
            day_formatted = day.strftime('%Y-%m-%d')
            labels.append(day.strftime('%a'))  # Abbreviated day name
            data.append(review_counts.get(day_formatted, 0))
        
        return jsonify({
            'labels': labels,
            'data': data
        })
    except Exception as e:
        app.logger.error(f"Error in study progress data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/demo-flashcards')
def demo_flashcards():
    # Sample flashcards for demo - no database required
    demo_cards = [
        {
            'id': 1,
            'front': 'What is the capital of France?',
            'back': 'Paris',
            'category': 'Geography'
        },
        {
            'id': 2,
            'front': 'What is the chemical symbol for water?',
            'back': 'H₂O',
            'category': 'Chemistry'
        },
        {
            'id': 3,
            'front': 'Who wrote "Romeo and Juliet"?',
            'back': 'William Shakespeare',
            'category': 'Literature'
        },
        {
            'id': 4,
            'front': 'What is the Pythagorean theorem?',
            'back': 'In a right triangle, the square of the hypotenuse equals the sum of the squares of the other two sides (a² + b² = c²)',
            'category': 'Mathematics'
        },
        {
            'id': 5,
            'front': 'What is photosynthesis?',
            'back': 'The process by which green plants use sunlight to synthesize nutrients from carbon dioxide and water.',
            'category': 'Biology'
        }
    ]
    
    return render_template('demo_flashcards.html', demo_cards=demo_cards)

# Application entry point - using port 8000 to avoid AirPlay conflict
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
