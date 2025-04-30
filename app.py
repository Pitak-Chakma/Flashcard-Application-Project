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
    if app.config['STORAGE_BACKEND'] == 'sqlite':
        return User.query.get(int(user_id))
    else:
        # For Supabase
        try:
            # Get all users and find the one we need
            # This avoids potential RLS issues
            response = db_adapter.supabase.client.table('users').select('*').execute()
            
            user_data = None
            if response.data:
                for user_record in response.data:
                    if user_record.get('id') == int(user_id):
                        user_data = user_record
                        break
            
            if user_data:
                user = User()
                user.id = user_data['id']
                user.username = user_data['username']
                user.email = user_data['email']
                user.password = user_data['password']
                role_value = user_data.get('role', 'user')
                if isinstance(role_value, UserRole):
                    user.role = role_value
                else:
                    try:
                        user.role = UserRole(role_value)
                    except Exception:
                        user.role = UserRole.USER
                return user
            return None
        except Exception as e:
            app.logger.error(f"Error loading user from Supabase: {str(e)}")
            return None

# Create folders if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Helper function to log activity
def log_activity(user_id, action, details=None):
    try:
        with app.app_context():
            # Get database adapter
            db_adapter = DatabaseAdapter()
            db_adapter.log_activity(user_id, action, details)
    except Exception as e:
        # Log the error but don't let it disrupt the application flow
        app.logger.error(f"Error logging activity: {action} - {str(e)}")
        # Don't re-raise the exception so the application can continue

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
        # Check if email already exists
        existing_user = None
        if app.config['STORAGE_BACKEND'] == 'sqlite':
            existing_user = User.query.filter_by(email=form.email.data).first()
        else:
            # For Supabase
            response = db_adapter.supabase.client.table('users').select('*').eq('email', form.email.data).execute()
            if response.data and len(response.data) > 0:
                existing_user = True
        
        if existing_user:
            flash('Email already registered. Please use a different email.', 'danger')
            return render_template('register.html', form=form)
            
        hashed_password = generate_password_hash(form.password.data)
        
        # Create user data dictionary
        user_data = {
            'username': form.username.data,
            'email': form.email.data,
            'password': hashed_password,
            'role': 'user',  # Default role
            'date_joined': datetime.utcnow().isoformat() if app.config['STORAGE_BACKEND'] == 'supabase' else datetime.utcnow()
        }
        
        # Add to database using adapter
        user = db_adapter.create_user(user_data)
        
        # Log activity
        if user:
            log_activity(user.id if hasattr(user, 'id') else user['id'], "User registered")
            flash('Your account has been created! You can now log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Registration failed. Please try again.', 'danger')
    
    return render_template('register.html', form=form)

# User login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # Get database adapter
        db_adapter = DatabaseAdapter()
        
        try:
            # Get user by email or username
            user_found = None
            login_identifier = form.email.data  # This field now accepts either email or username
            
            if app.config['STORAGE_BACKEND'] == 'sqlite':
                # Try to find user by email first
                user = User.query.filter_by(email=login_identifier).first()
                if not user:
                    # If not found by email, try username
                    user = User.query.filter_by(username=login_identifier).first()
                if user:
                    user_found = user
            else:
                # For Supabase
                app.logger.info(f"Attempting to log in with identifier: {login_identifier}")
                
                # Try to find user by email first
                response = db_adapter.supabase.client.table('users').select('*').eq('email', login_identifier).execute()
                
                # If not found by email, try username
                if not response.data or len(response.data) == 0:
                    response = db_adapter.supabase.client.table('users').select('*').eq('username', login_identifier).execute()
                
                app.logger.info(f"User query response: {response}")
                
                if response.data and len(response.data) > 0:
                    user_found = response.data[0]
                    app.logger.info(f"User found: {user_found['username']}")
            
            # Process login regardless of backend
            if user_found:
                # Check password
                password_field = user_found.password if hasattr(user_found, 'password') else user_found.get('password')
                password_input = form.password.data
                
                if check_password_hash(password_field, password_input):
                    # Create a User object for Flask-Login if needed
                    if app.config['STORAGE_BACKEND'] == 'sqlite':
                        user = user_found  # Already a User object
                    else:
                        # Create User object from dict
                        user = User()
                        user.id = user_found['id']
                        user.username = user_found['username']
                        user.email = user_found['email']
                        user.password = user_found['password']
                        user.role = user_found.get('role', 'user')
                    
                    # Login the user
                    login_user(user, remember=form.remember.data)
                    
                    # Log the activity
                    try:
                        log_activity(user.id, "User logged in")
                    except Exception as log_error:
                        app.logger.error(f"Error logging login activity: {str(log_error)}")
                    
                    # If username is 'root', treat as admin and redirect to admin dashboard
                    if user.username == 'root':
                        # Optionally, set role to admin if not already
                        if user.role != UserRole.ADMIN:
                            user.role = UserRole.ADMIN
                            if app.config['STORAGE_BACKEND'] == 'sqlite':
                                db.session.commit()
                            else:
                                # For Supabase, update role in the database
                                db_adapter.supabase.client.table('users').update({'role': 'admin'}).eq('id', user.id).execute()
                                user.role = UserRole.ADMIN
                        app.logger.info("Root user logged in, redirecting to admin dashboard.")
                        return redirect(url_for('admin_dashboard'))
                    # Otherwise, normal redirect
                    next_page = request.args.get('next')
                    app.logger.info(f"Login successful, redirecting to: {next_page if next_page else 'dashboard'}")
                    return redirect(next_page) if next_page else redirect(url_for('dashboard'))
                else:
                    app.logger.info("Password verification failed")
                    flash('Login unsuccessful. Please check username/email and password.', 'danger')
            else:
                app.logger.info(f"No user found with identifier: {login_identifier}")
                flash('Login unsuccessful. Please check username/email and password.', 'danger')
        except Exception as e:
            app.logger.error(f"Error during login: {str(e)}")
            flash(f'Login error: {str(e)}', 'danger')
    
    return render_template('login.html', form=form)

# User logout route
@app.route('/logout')
@login_required
def logout():
    # Store user_id before logout since current_user won't be available after logout_user()
    user_id = current_user.id
    
    # First logout the user
    logout_user()
    
    try:
        # Then log the activity
        log_activity(user_id, "User logged out")
    except Exception as e:
        # If there's an error with logging activity, just continue
        # This prevents the postgrest.exceptions.APIError from affecting the user experience
        app.logger.error(f"Error logging logout activity: {str(e)}")
    
    return redirect(url_for('index'))

# User dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    # Get database adapter
    db_adapter = DatabaseAdapter()
    
    # Get user stats
    if app.config['STORAGE_BACKEND'] == 'sqlite':
        user_cards = Card.query.filter_by(user_id=current_user.id).count()
        reviews_today = CardReview.query.filter(
            CardReview.user_id == current_user.id,
            CardReview.next_review <= datetime.utcnow()
        ).count()
        achievements = UserAchievement.query.filter_by(user_id=current_user.id).all()
    else:
        # Supabase: count cards
        response = db_adapter.supabase.client.table('cards').select('id', count='exact').eq('user_id', current_user.id).execute()
        user_cards = response.count if hasattr(response, 'count') else 0
        # Count reviews due today
        now_iso = datetime.utcnow().isoformat()
        review_response = db_adapter.supabase.client.table('card_reviews').select('id', count='exact').eq('user_id', current_user.id).lte('next_review', now_iso).execute()
        reviews_today = review_response.count if hasattr(review_response, 'count') else 0
        # Get achievements
        ach_response = db_adapter.supabase.client.table('user_achievements').select('*').eq('user_id', current_user.id).execute()
        achievements = [db_adapter._supabase_to_model(a, UserAchievement) for a in ach_response.data] if ach_response.data else []
    
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
        # Create a user_data dictionary for the update
        user_data = {
            'username': form.username.data,
            'email': form.email.data
        }
        
        # Handle profile pic upload
        if form.profile_pic.data:
            picture_file = save_profile_picture(form.profile_pic.data)
            user_data['profile_pic'] = picture_file
        
        # Get database adapter
        db_adapter = DatabaseAdapter()
        
        # Update the user using the adapter
        db_adapter.update_user(current_user.id, user_data)
        
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
        try:
            # Get database adapter
            db_adapter = DatabaseAdapter()
            
            if app.config['STORAGE_BACKEND'] == 'sqlite':
                # Create the card using SQLAlchemy
                card = Card(
                    question=form.question.data,
                    answer=form.answer.data,
                    is_public=form.is_public.data,
                    user_id=current_user.id
                )
                
                # Process tags
                tags = []
                if form.tags.data:
                    tag_names = [tag.strip() for tag in form.tags.data.split(',')]
                    for tag_name in tag_names:
                        # Check if tag exists, create if it doesn't
                        tag = Tag.query.filter_by(name=tag_name).first()
                        if not tag:
                            tag = Tag(name=tag_name)
                            db.session.add(tag)
                        card.tags.append(tag)
                        tags.append(tag)
                
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
            else:
                # For Supabase, use the adapter
                # Prepare card data - omit created_at and updated_at as they're handled by default values in Supabase
                card_data = {
                    'question': form.question.data,
                    'answer': form.answer.data,
                    'is_public': form.is_public.data,
                    'user_id': current_user.id
                }
                
                # Process tags
                tags = []
                if form.tags.data:
                    tag_names = [tag.strip() for tag in form.tags.data.split(',')]
                    for tag_name in tag_names:
                        # Check if tag exists, create if it doesn't
                        tag_response = db_adapter.supabase.client.table('tags').select('*').eq('name', tag_name).execute()
                        
                        if not tag_response.data or len(tag_response.data) == 0:
                            # Create new tag
                            tag_data = {'name': tag_name, 'color': '#3498db'}
                            tag_response = db_adapter.supabase.client.table('tags').insert(tag_data).execute()
                            
                        tag = tag_response.data[0] if tag_response.data else None
                        if tag:
                            tags.append(tag)
                
                # Create the card using the adapter
                card = db_adapter.create_card(card_data, tags)
                
                # Create initial review interval
                review_data = {
                    'card_id': card.id if hasattr(card, 'id') else card['id'],
                    'user_id': current_user.id,
                    'ease_factor': 2.5,
                    'interval': 1,
                    'next_review': datetime.utcnow().isoformat()
                }
                db_adapter.create_review(review_data)
            
            # Log the activity with error handling
            try:
                card_id = card.id if hasattr(card, 'id') else card['id']
                log_activity(current_user.id, "Created flashcard", f"Card ID: {card_id}")
            except Exception as log_error:
                app.logger.error(f"Error logging card creation activity: {str(log_error)}")
            
            flash('Your flashcard has been created!', 'success')
            return redirect(url_for('view_cards'))
        except Exception as e:
            app.logger.error(f"Error creating flashcard: {str(e)}")
            flash(f'Error creating flashcard: {str(e)}', 'danger')
            return render_template('create_card.html', form=form)
    
    return render_template('create_card.html', form=form)

# View flashcards
@app.route('/view_cards')
@login_required
def view_cards():
    try:
        # Get database adapter
        db_adapter = DatabaseAdapter()
        
        search_form = SearchCardForm()
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '')
        tag_filter = request.args.get('tag', '')
        
        # Get user's cards using the database adapter
        if app.config['STORAGE_BACKEND'] == 'sqlite':
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
        else:
            # For Supabase, use the adapter
            app.logger.info(f"Getting cards for user {current_user.id} from Supabase")
            
            # Get all user cards
            tag_id = None
            if tag_filter:
                # Get tag ID if tag filter is provided
                tag_response = db_adapter.supabase.client.table('tags').select('id').eq('name', tag_filter).execute()
                if tag_response.data and len(tag_response.data) > 0:
                    tag_id = tag_response.data[0]['id']
            
            # Get cards using the adapter
            all_cards = db_adapter.get_user_cards(current_user.id, tag_id=tag_id)
            app.logger.info(f"Retrieved {len(all_cards) if all_cards else 0} cards from Supabase")
            
            # Apply search filter if provided
            if search and all_cards:
                filtered_cards = []
                for card in all_cards:
                    question = card.question if hasattr(card, 'question') else card.get('question', '')
                    answer = card.answer if hasattr(card, 'answer') else card.get('answer', '')
                    if search.lower() in question.lower() or search.lower() in answer.lower():
                        filtered_cards.append(card)
                all_cards = filtered_cards
            
            # Manual pagination
            per_page = 10
            total_cards = len(all_cards) if all_cards else 0
            total_pages = (total_cards + per_page - 1) // per_page if total_cards > 0 else 1
            page = min(page, total_pages)
            
            # Sort cards by created_at (descending) if available
            if all_cards:
                # Sort by created_at if available, otherwise don't sort
                try:
                    all_cards.sort(key=lambda c: c.created_at if hasattr(c, 'created_at') else c.get('created_at', ''), reverse=True)
                except Exception as sort_error:
                    app.logger.error(f"Error sorting cards: {str(sort_error)}")
            
            # Create a paginated object similar to SQLAlchemy's pagination
            start_idx = (page - 1) * per_page
            end_idx = min(start_idx + per_page, total_cards)
            
            # Create a simple pagination object
            class SimplePagination:
                def __init__(self, items, page, per_page, total):
                    self.items = items
                    self.page = page
                    self.per_page = per_page
                    self.total = total
                    self.pages = (total + per_page - 1) // per_page if total > 0 else 1
                
                def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
                    last = 0
                    for num in range(1, self.pages + 1):
                        if num <= left_edge or \
                           (num > self.page - left_current - 1 and num < self.page + right_current) or \
                           num > self.pages - right_edge:
                            if last + 1 != num:
                                yield None
                            yield num
                            last = num
                
                @property
                def has_prev(self):
                    return self.page > 1
                
                @property
                def has_next(self):
                    return self.page < self.pages
                
                @property
                def prev_num(self):
                    return self.page - 1 if self.has_prev else None
                
                @property
                def next_num(self):
                    return self.page + 1 if self.has_next else None
            
            # Create pagination object
            current_page_items = all_cards[start_idx:end_idx] if all_cards else []
            cards = SimplePagination(current_page_items, page, per_page, total_cards)
            
            # Get all tags for filter dropdown
            tags_response = db_adapter.supabase.client.table('tags')\
                .select('*')\
                .execute()
            
            all_tags = []
            if tags_response.data:
                # Convert to Tag objects
                for tag_data in tags_response.data:
                    tag = Tag()
                    tag.id = tag_data['id']
                    tag.name = tag_data['name']
                    tag.color = tag_data.get('color', '#3498db')
                    all_tags.append(tag)
        
        app.logger.info(f"Rendering view_cards template with {len(cards.items) if hasattr(cards, 'items') else 0} cards")
        return render_template('view_cards.html', cards=cards, search_form=search_form, 
                            all_tags=all_tags, current_search=search, current_tag=tag_filter)
    except Exception as e:
        app.logger.error(f"Error in view_cards: {str(e)}")
        flash(f"Error loading cards: {str(e)}", 'danger')
        return render_template('view_cards.html', cards=None, search_form=search_form, 
                            all_tags=[], current_search=search, current_tag=tag_filter)

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
    
    # Get learning efficiency for the user
    efficiency = SpacedRepetition.get_learning_efficiency(
        current_user.id
    )
    
    return render_template('study.html', 
                          due_count=due_count, 
                          new_count=new_count,
                          cards_due=due_count,
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
    try:
        app.logger.info(f"Updating review {review_id} for user {current_user.id}")
        
        # Get the review using the database adapter
        review = db_adapter.get_review(review_id)
        if not review:
            app.logger.error(f"Review {review_id} not found")
            return jsonify({'status': 'error', 'message': 'Review not found'}), 404
        
        # Check if user owns the review
        if review.user_id != current_user.id:
            app.logger.error(f"Unauthorized access to review {review_id} by user {current_user.id}")
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
        
        # Get difficulty rating from request (1-4 scale)
        try:
            data = request.get_json()
            if not data:
                app.logger.error(f"No JSON data in request for review {review_id}")
                return jsonify({'status': 'error', 'message': 'No data provided'}), 400
                
            difficulty = int(data.get('difficulty', 3))
            if difficulty < 1 or difficulty > 4:
                app.logger.error(f"Invalid difficulty value: {difficulty}")
                return jsonify({'status': 'error', 'message': 'Invalid difficulty value'}), 400
        except Exception as e:
            app.logger.error(f"Error parsing request data: {str(e)}")
            return jsonify({'status': 'error', 'message': f'Invalid request data: {str(e)}'}), 400
        
        # Use the spaced repetition service to calculate the next interval and ease factor
        try:
            new_interval, new_ease_factor = SpacedRepetition.calculate_next_interval(
                current_interval=review.interval,
                ease_factor=review.ease_factor,
                difficulty=difficulty
            )
            
            # Prepare the updated review data
            next_review_date = SpacedRepetition.calculate_next_review_date(new_interval)
            
            # Format datetime objects properly for database storage
            current_time = datetime.utcnow()
            # Format with exactly 6 decimal places for microseconds
            formatted_time = current_time.strftime('%Y-%m-%dT%H:%M:%S.%f')
            formatted_next_review = next_review_date.strftime('%Y-%m-%dT%H:%M:%S.%f')
            
            review_data = {
                'interval': new_interval,
                'ease_factor': new_ease_factor,
                'last_reviewed': current_time,  # SQLite will use the datetime object
                'next_review': next_review_date  # SQLite will use the datetime object
            }
            
            # For Supabase, we need to use formatted strings
            if app.config['STORAGE_BACKEND'] == 'supabase':
                review_data['last_reviewed'] = formatted_time
                review_data['next_review'] = formatted_next_review
            
            # Update the review using the database adapter
            updated_review = db_adapter.update_review(review_id, review_data)
            if not updated_review:
                app.logger.error(f"Failed to update review {review_id}")
                return jsonify({'status': 'error', 'message': 'Failed to update review'}), 500
                
            # Log the activity with error handling
            try:
                log_activity(current_user.id, "Reviewed flashcard", 
                            f"Card ID: {review.card_id}, Difficulty: {difficulty}, Next review in {new_interval} days")
            except Exception as log_error:
                app.logger.error(f"Error logging review activity: {str(log_error)}")
            
            # Check for achievements
            try:
                check_review_achievements(current_user.id)
            except Exception as ach_error:
                app.logger.error(f"Error checking achievements: {str(ach_error)}")
            
            # Get learning efficiency metrics using the updated SpacedRepetition service
            try:
                efficiency = SpacedRepetition.get_learning_efficiency(user_id=current_user.id)
            except Exception as eff_error:
                app.logger.error(f"Error calculating efficiency: {str(eff_error)}")
                efficiency = {
                    "total_reviews": 0,
                    "average_ease": 0,
                    "retention_rate": 0,
                    "review_streak": 0
                }
            
            app.logger.info(f"Successfully updated review {review_id}")
            
            # Format the next review date safely
            if isinstance(next_review_date, str):
                # If it's already a string, just use the date part
                next_review_formatted = next_review_date.split('T')[0] if 'T' in next_review_date else next_review_date
            elif hasattr(next_review_date, 'strftime'):
                # If it's a datetime object, format it
                next_review_formatted = next_review_date.strftime('%Y-%m-%d')
            else:
                # Fallback
                next_review_formatted = str(next_review_date)
                
            return jsonify({
                'status': 'success',
                'new_interval': new_interval,
                'new_ease_factor': round(new_ease_factor, 2),
                'next_review': next_review_formatted,
                'efficiency': efficiency
            })
            
        except Exception as calc_error:
            app.logger.error(f"Error calculating next interval: {str(calc_error)}")
            return jsonify({'status': 'error', 'message': f'Error calculating review: {str(calc_error)}'}), 500
            
    except Exception as e:
        app.logger.error(f"Unexpected error in update_review: {str(e)}")
        return jsonify({'status': 'error', 'message': 'An unexpected error occurred'}), 500

# Helper function to check and award review-based achievements
def check_review_achievements(user_id):
    # Get database adapter
    db_adapter = DatabaseAdapter()
    
    # Count total reviews
    if app.config['STORAGE_BACKEND'] == 'sqlite':
        review_count = CardReview.query.filter(
            CardReview.user_id == user_id,
            CardReview.last_reviewed != None
        ).count()
    else:
        # For Supabase, use the client to count reviews
        response = db_adapter.supabase.client.table('card_reviews')\
            .select('id', count='exact')\
            .eq('user_id', user_id)\
            .not_('last_reviewed', 'is', 'null')\
            .execute()
        review_count = response.count if hasattr(response, 'count') else 0
    
    # Milestone achievements
    milestones = {
        10: "Beginner Reviewer",
        50: "Intermediate Reviewer", 
        100: "Advanced Reviewer",
        500: "Master Reviewer"
    }
    
    for count, name in milestones.items():
        if review_count >= count:
            # Check if achievement exists and if user already has it
            if app.config['STORAGE_BACKEND'] == 'sqlite':
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
            else:
                # For Supabase, use the client to check achievements
                achievement_response = db_adapter.supabase.client.table('achievements')\
                    .select('*')\
                    .eq('name', name)\
                    .execute()
                
                if not achievement_response.data or len(achievement_response.data) == 0:
                    # Create achievement if it doesn't exist
                    achievement_data = {
                        'name': name,
                        'description': f"Completed {count} flashcard reviews",
                        'badge_image': f"badge_{count}.png"
                    }
                    achievement_response = db_adapter.supabase.client.table('achievements')\
                        .insert(achievement_data)\
                        .execute()
                
                achievement = achievement_response.data[0] if achievement_response.data else None
                
                if achievement:
                    # Check if user already has this achievement
                    user_achievement_response = db_adapter.supabase.client.table('user_achievements')\
                        .select('*')\
                        .eq('user_id', user_id)\
                        .eq('achievement_id', achievement['id'])\
                        .execute()
                    
                    user_achievement = user_achievement_response.data[0] if user_achievement_response.data else None
            
            if not user_achievement:
                # Award achievement
                if app.config['STORAGE_BACKEND'] == 'sqlite':
                    new_achievement = UserAchievement(
                        user_id=user_id,
                        achievement_id=achievement.id
                    )
                    db.session.add(new_achievement)
                    db.session.commit()
                else:
                    # For Supabase, use the adapter to award achievement
                    achievement_id = achievement['id'] if isinstance(achievement, dict) else achievement.id
                    db_adapter.award_achievement(user_id, achievement_id)
                
                log_activity(user_id, "Earned achievement", f"Achievement: {name}")

# Admin dashboard
@app.route('/admin')
@login_required
def admin_dashboard():
    # Check if user is admin
    if current_user.role != UserRole.ADMIN:
        abort(403)  # Forbidden
    
    # Get database adapter
    db_adapter = DatabaseAdapter()
    
    # Get stats for admin dashboard
    if app.config['STORAGE_BACKEND'] == 'sqlite':
        total_users = User.query.count()
        total_cards = Card.query.count()
        total_reviews = CardReview.query.count()
        
        # Get recent activity logs
        activity_logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(50).all()
        
        # Get user list
        users = User.query.all()
    else:
        # For Supabase, use the client to get counts and data
        users_response = db_adapter.supabase.client.table('users').select('*', count='exact').execute()
        total_users = users_response.count if hasattr(users_response, 'count') else len(users_response.data)
        users = [db_adapter._supabase_to_model(user_data, User) for user_data in users_response.data] if users_response.data else []
        # Convert date_joined to datetime if needed
        from datetime import datetime
        for user in users:
            if hasattr(user, 'date_joined') and isinstance(user.date_joined, str):
                try:
                    user.date_joined = datetime.fromisoformat(user.date_joined)
                except Exception:
                    user.date_joined = None
        
        cards_response = db_adapter.supabase.client.table('cards').select('*', count='exact').execute()
        total_cards = cards_response.count if hasattr(cards_response, 'count') else 0
        
        reviews_response = db_adapter.supabase.client.table('card_reviews').select('*', count='exact').execute()
        total_reviews = reviews_response.count if hasattr(reviews_response, 'count') else 0
        
        # Get recent activity logs
        logs_response = db_adapter.supabase.client.table('activity_logs').select('*').order('timestamp', desc=True).limit(50).execute()
        activity_logs = [db_adapter._supabase_to_model(log_data, ActivityLog) for log_data in logs_response.data] if logs_response.data else []
        # Convert timestamp to datetime if needed
        from datetime import datetime
        for log in activity_logs:
            if hasattr(log, 'timestamp') and isinstance(log.timestamp, str):
                try:
                    log.timestamp = datetime.fromisoformat(log.timestamp)
                except Exception:
                    log.timestamp = None
    
    return render_template('admin.html', total_users=total_users, total_cards=total_cards,
                          total_reviews=total_reviews, activity_logs=activity_logs)

@app.route('/admin/users')
@login_required
def admin_user_management():
    if current_user.role != UserRole.ADMIN:
        abort(403)
    db_adapter = DatabaseAdapter()
    if app.config['STORAGE_BACKEND'] == 'sqlite':
        total_users = User.query.count()
        users = User.query.all()
    else:
        users_response = db_adapter.supabase.client.table('users').select('*', count='exact').execute()
        total_users = users_response.count if hasattr(users_response, 'count') else len(users_response.data)
        users = [db_adapter._supabase_to_model(user_data, User) for user_data in users_response.data] if users_response.data else []
        from datetime import datetime
        for user in users:
            if hasattr(user, 'date_joined') and isinstance(user.date_joined, str):
                try:
                    user.date_joined = datetime.fromisoformat(user.date_joined)
                except Exception:
                    user.date_joined = None
    return render_template('admin_user_management.html', users=users, total_users=total_users)

# Admin: edit user
@app.route('/admin/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_user(user_id):
    # Check if user is admin
    if current_user.role != UserRole.ADMIN:
        abort(403)  # Forbidden
    
    # Get database adapter
    db_adapter = DatabaseAdapter()
    
    # Get the user using the adapter
    user = db_adapter.get_user(user_id)
    if not user:
        abort(404)
    
    if request.method == 'POST':
        # Prepare user data for update
        user_data = {
            'username': request.form.get('username'),
            'email': request.form.get('email'),
            'role': request.form.get('role')
        }
        
        # Update user using the adapter
        db_adapter.update_user(user_id, user_data)
        
        # Log the activity
        log_activity(current_user.id, "Admin edited user", f"User ID: {user_id}")
        flash('User has been updated!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin_edit_user.html', user=user, roles=UserRole)

# Initialize database
@app.before_first_request
def create_tables():
    # Get database adapter
    db_adapter = DatabaseAdapter()
    
    if app.config['STORAGE_BACKEND'] == 'sqlite':
        # For SQLite, create tables using SQLAlchemy
        db.create_all()
        
        # Create admin user if not exists
        admin = User.query.filter_by(email='admin@example.com').first()
        if not admin:
            hashed_password = generate_password_hash('admin123')
            admin = User(username='admin', email='admin@example.com', 
                        password=hashed_password, role=UserRole.ADMIN)
            db.session.add(admin)
            db.session.commit()
            
        # Create superuser admin if not exists
        superuser = User.query.filter_by(username='root').first()
        if not superuser:
            hashed_password = generate_password_hash('T9x!rV@5mL#8wQz&Kd3')
            superuser = User(username='root', email='root@example.com', 
                        password=hashed_password, role=UserRole.ADMIN)
            db.session.add(superuser)
            db.session.commit()
    else:
        # For Supabase, check if admin user exists
        admin_response = db_adapter.supabase.client.table('users').select('*').eq('email', 'admin@example.com').execute()
        
        if not admin_response.data or len(admin_response.data) == 0:
            # Create admin user if not exists
            hashed_password = generate_password_hash('admin123')
            admin_data = {
                'username': 'admin',
                'email': 'admin@example.com',
                'password': hashed_password,
                'role': 'admin',
                'date_joined': datetime.utcnow().isoformat()
            }
            db_adapter.create_user(admin_data)
            
        # Check if superuser admin exists
        superuser_response = db_adapter.supabase.client.table('users').select('*').eq('username', 'root').execute()
        
        if not superuser_response.data or len(superuser_response.data) == 0:
            # Create superuser admin if not exists
            hashed_password = generate_password_hash('T9x!rV@5mL#8wQz&Kd3')
            superuser_data = {
                'username': 'root',
                'email': 'root@example.com',
                'password': hashed_password,
                'role': 'admin',
                'date_joined': datetime.utcnow().isoformat()
            }
            db_adapter.create_user(superuser_data)


@app.route('/all-link')
@login_required
def all_links():
    # Check if the user is the superuser (root)
    if current_user.username != 'root':
        abort(403)  # Forbidden
    
    # Get all routes in the application
    routes = []
    for rule in app.url_map.iter_rules():
        # Skip static files and error handlers
        if not rule.endpoint.startswith('static') and not rule.endpoint.startswith('_'):
            routes.append({
                'endpoint': rule.endpoint,
                'methods': list(rule.methods),
                'path': str(rule),
                'arguments': list(rule.arguments)
            })
    
    # Sort routes by endpoint name
    routes.sort(key=lambda x: x['endpoint'])
    
    return render_template('all_links.html', routes=routes)


@app.route('/info')
def info():
    # Project and personal information
    info_data = {
        'name': 'Pitak Chakma',
        'id': '2220162',
        'personal_notion_page': 'https://www.notion.so/Flash_Card-Web-Application-Project-Spring-2025-1ab3cb42318c8005a389e977475535b1?pvs=4',
        'github_id': 'https://github.com/Pitak-Chakma',
        'project_github_link': 'https://github.com/Pitak-Chakma/Flashcard-Application-Project'
    }
    
    # Return as HTML page
    return render_template('info.html', info=info_data)


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

# Application entry point - using port 8001 to avoid conflicts
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=True)
