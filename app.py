from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure random string

# Database setup
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS flashcards 
                 (id INTEGER PRIMARY KEY, user_id INTEGER, front TEXT, back TEXT, tags TEXT,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

# Home route
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('signin'))

# Sign-up route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        try:
            c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            return redirect(url_for('signin'))
        except sqlite3.IntegrityError:
            return 'Username already exists'
        finally:
            conn.close()
    return render_template('signup.html')

# Sign-in route
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            return redirect(url_for('dashboard'))
        return 'Invalid credentials'
    return render_template('signin.html')

# Dashboard route with flashcard functionality
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    # Get username
    c.execute('SELECT username FROM users WHERE id = ?', (session['user_id'],))
    username = c.fetchone()[0]
    
    # Handle flashcard creation
    if request.method == 'POST' and 'front' in request.form:
        front = request.form['front']
        back = request.form['back']
        tags = request.form['tags']
        user_id = session['user_id']
        c.execute('INSERT INTO flashcards (user_id, front, back, tags) VALUES (?, ?, ?, ?)', 
                  (user_id, front, back, tags))
        conn.commit()
    
    # Fetch user's flashcards
    c.execute('SELECT id, front, back, tags FROM flashcards WHERE user_id = ?', (session['user_id'],))
    flashcards = c.fetchall()
    conn.close()
    
    return render_template('dashboard.html', username=username, flashcards=flashcards)

# Edit flashcard route
@app.route('/edit/<int:flashcard_id>', methods=['POST'])
def edit_flashcard(flashcard_id):
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    front = request.form['front']
    back = request.form['back']
    tags = request.form['tags']
    c.execute('UPDATE