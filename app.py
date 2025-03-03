from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, g
import sqlite3
import os
import json
import datetime
from werkzeug.exceptions import abort
from functools import wraps
from models import User, Tag, Flashcard, Progress, Notification, Reward
from config import Config
from helpers import login_required, calculate_next_review, check_achievements

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Ensure the database exists
def init_db():
    if not os.path.exists(app.config['DATABASE']):
        conn = sqlite3.connect(app.config['DATABASE'])
        with app.open_resource('schema.sql', mode='r') as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()

with app.app_context():
    init_db()

# Database connection helper
def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if not username or not email or not password:
            flash('All fields are required', 'error')
            return render_template('auth/register.html')
        
        if User.create(username, email, password):
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Username or email already exists', 'error')
    
    return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.authenticate(username, password)
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    tags = Tag.get_by_user(user_id)
    stats = Progress.get_user_stats(user_id)

    # Ensure daily_reviews and daily_success_rates are initialized
    stats['daily_reviews'] = stats.get('daily_reviews', [])
    stats['daily_success_rates'] = stats.get('daily_success_rates', [])

    return render_template(
        'dashboard.html',
        tags=tags,
        stats=stats
    )


@app.route('/tags/create', methods=['GET', 'POST'])
@login_required
def create_tag():
    user_id = session['user_id']
    
    if request.method == 'POST':
        tag_name = request.form['tag_name']
        is_public = 'is_public' in request.form  # Checkbox for public/private

        # Validate inputs
        if not tag_name:
            flash('Tag name is required', 'error')
            return render_template('tags/create.html')

        # Create the tag
        Tag.create(user_id, tag_name, is_public)
        flash('Tag created successfully', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('tags/create.html')


@app.route('/tags/<int:tag_id>/update', methods=['POST'])
@login_required
def update_tag(tag_id):
    user_id = session['user_id']
    is_public = 'is_public' in request.form
    
    Tag.update_visibility(tag_id, user_id, is_public)
    flash('Tag visibility updated', 'success')
    
    return redirect(url_for('dashboard'))

@app.route('/tags/<int:tag_id>')
@login_required
def view_tag(tag_id):
    user_id = session['user_id']
    flashcards = Flashcard.get_by_tag(tag_id, user_id)
    
    return render_template('flashcards/view.html', flashcards=flashcards, tag_id=tag_id)

@app.route('/flashcards/create', methods=['GET', 'POST'])
@login_required
def create_flashcard():
    user_id = session['user_id']
    
    if request.method == 'POST':
        tag_id = request.form['tag_id']
        question = request.form['question']
        correct_answer = request.form['correct_answer']
        options = request.form.getlist('options[]')  # Assuming options are sent as a list
        is_public = 'is_public' in request.form  # Checkbox for public/private

        # Validate inputs
        if not tag_id or not question or not correct_answer or not options:
            flash('All fields are required', 'error')
            tags = Tag.get_by_user(user_id)
            return render_template('flashcards/create.html', tags=tags)

        # Create the flashcard
        Flashcard.create(user_id, tag_id, question, options, correct_answer, is_public)
        flash('Flashcard created successfully', 'success')
        return redirect(url_for('view_tag', tag_id=tag_id))
    
    tags = Tag.get_by_user(user_id)
    return render_template('flashcards/create.html', tags=tags)


@app.route('/flashcards/test/<int:tag_id>')
@login_required
def test_flashcards(tag_id):
    user_id = session['user_id']
    flashcards = Flashcard.get_by_tag(tag_id, user_id)
    
    # Get a random flashcard from this tag
    import random
    if flashcards:
        card = random.choice(flashcards)
        return render_template('flashcards/test.html', card=card, tag_id=tag_id)
    else:
        flash('No flashcards found in this tag', 'error')
        return redirect(url_for('dashboard'))

@app.route('/flashcards/answer', methods=['POST'])
@login_required
def answer_flashcard():
    user_id = session['user_id']
    flashcard_id = request.form['flashcard_id']
    tag_id = request.form['tag_id']
    selected_answer = request.form['selected_answer']
    correct_answer = request.form['correct_answer']
    
    is_correct = selected_answer == correct_answer
    Flashcard.update_review_schedule(flashcard_id, user_id, is_correct)
    
    # Check for achievements
    stats = Progress.get_user_stats(user_id)
    check_achievements(user_id, stats)
    
    if is_correct:
        flash('Correct answer! Good job!', 'success')
    else:
        flash(f'Incorrect. The correct answer was: {correct_answer}', 'error')
    
    return redirect(url_for('test_flashcards', tag_id=tag_id))

@app.route('/stats')
@login_required
def view_stats():
    user_id = session['user_id']
    stats = Progress.get_user_stats(user_id)
    
    # Add additional data for charts
    conn = get_db_connection()
    
    # Get daily review counts for the last 7 days
    seven_days_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).isoformat()
    daily_reviews = []
    daily_success_rates = []
    
    for i in range(7):
        day = (datetime.datetime.now() - datetime.timedelta(days=i)).strftime('%Y-%m-%d')
        day_start = f"{day}T00:00:00"
        day_end = f"{day}T23:59:59"
        
        # Count reviews on this day
        reviews = conn.execute(
            '''SELECT COUNT(*) as count FROM user_progress 
               WHERE user_id = ? AND reviewed_at BETWEEN ? AND ?''',
            (user_id, day_start, day_end)
        ).fetchone()['count']
        
        # Count successful reviews on this day
        if reviews > 0:
            successful = conn.execute(
                '''SELECT COUNT(*) as count FROM user_progress 
                   WHERE user_id = ? AND reviewed_at BETWEEN ? AND ? AND is_correct = 1''',
                (user_id, day_start, day_end)
            ).fetchone()['count']
            success_rate = round((successful / reviews) * 100, 1)
        else:
            success_rate = 0
        
        daily_reviews.insert(0, reviews)
        daily_success_rates.insert(0, success_rate)
    
    stats['daily_reviews'] = daily_reviews
    stats['daily_success_rates'] = daily_success_rates
    
    # Get upcoming reviews
    now = datetime.datetime.now()
    upcoming = {}
    max_count = 0
    
    # Get next 7 days
    for i in range(7):
        day = (now + datetime.timedelta(days=i)).strftime('%m/%d')
        day_start = (now + datetime.timedelta(days=i)).strftime('%Y-%m-%d') + "T00:00:00"
        day_end = (now + datetime.timedelta(days=i)).strftime('%Y-%m-%d') + "T23:59:59"
        
        count = conn.execute(
            '''SELECT COUNT(*) as count FROM flashcards 
               WHERE user_id = ? AND next_review BETWEEN ? AND ?''',
            (user_id, day_start, day_end)
        ).fetchone()['count']
        
        upcoming[day] = count
        max_count = max(max_count, count)
    
    stats['upcoming_reviews'] = upcoming
    stats['max_daily_reviews'] = max_count
    
    # Get current max interval setting (would be in a settings table)
    stats['current_max_interval'] = 60  # Default value
    
    conn.close()
    
    return render_template('stats.html', stats=stats)

@app.route('/notifications/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    user_id = session['user_id']
    Notification.mark_as_read(notification_id, user_id)
    return redirect(url_for('dashboard'))

@app.route('/schedule-notifications', methods=['POST'])
@login_required
def schedule_notifications():
    user_id = session['user_id']
    interval_hours = int(request.form['interval_hours'])
    
    now = datetime.datetime.now()
    next_review = now + datetime.timedelta(hours=interval_hours)
    
    Notification.create(
        user_id,
        f"Time to review your flashcards!",
        scheduled_for=next_review.isoformat()
    )
    
    flash('Notification scheduled successfully', 'success')
    return redirect(url_for('dashboard'))

@app.route('/browse')
@login_required
def browse_public():
    public_tags = Tag.get_public_tags()
    return render_template('flashcards/browse.html', tags=public_tags)

@app.route('/update_flashcard_visibility/<int:flashcard_id>', methods=['POST'])
@login_required
def update_flashcard_visibility(flashcard_id):
    user_id = session['user_id']
    is_public = 'is_public' in request.form
    
    conn = get_db_connection()
    conn.execute(
        'UPDATE flashcards SET is_public = ? WHERE id = ? AND user_id = ?',
        (is_public, flashcard_id, user_id)
    )
    conn.commit()
    conn.close()
    
    flash('Flashcard visibility updated', 'success')
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/test_specific_flashcard/<int:flashcard_id>')
@login_required
def test_specific_flashcard(flashcard_id):
    user_id = session['user_id']
    
    conn = get_db_connection()
    card = conn.execute(
        '''SELECT * FROM flashcards 
           WHERE id = ? AND (user_id = ? OR is_public = 1)''',
        (flashcard_id, user_id)
    ).fetchone()
    conn.close()
    
    if not card:
        flash('Flashcard not found', 'error')
        return redirect(url_for('dashboard'))
    
    card_dict = dict(card)
    card_dict['options'] = json.loads(card_dict['options'])
    
    return render_template('flashcards/test.html', card=card_dict, tag_id=card_dict['tag_id'])

@app.route('/update_spaced_repetition', methods=['POST'])
@login_required
def update_spaced_repetition():
    user_id = session['user_id']
    max_interval = request.form.get('max_interval', 60)
    
    # In a real application, we would store this setting in a user_settings table
    # For now, we just acknowledge the request
    flash('Spaced repetition settings updated', 'success')
    return redirect(url_for('view_stats'))

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', 
                           error_code=404, 
                           error_message="The page you're looking for doesn't exist."), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', 
                           error_code=500, 
                           error_message="Something went wrong on our end."), 500

if __name__ == '__main__':
    app.run(debug=True)
