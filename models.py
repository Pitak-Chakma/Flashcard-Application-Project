import sqlite3
import json
import datetime
from werkzeug.security import generate_password_hash, check_password_hash

def get_db_connection():
    conn = sqlite3.connect('flashcards.db')
    conn.row_factory = sqlite3.Row
    return conn

class User:
    @staticmethod
    def create(username, email, password):
        conn = get_db_connection()
        # Explicitly specify the hashing method as pbkdf2:sha256
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        
        try:
            conn.execute(
                '''
                INSERT INTO users (username, email, password_hash)
                VALUES (?, ?, ?)
                ''',
                (username, email, password_hash)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Username or email already exists
            return False
        finally:
            conn.close()

    
    @staticmethod
    def authenticate(username, password):
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
    
        if user and check_password_hash(user['password_hash'], password):
            return dict(user)
        return None

    
    @staticmethod
    def get_by_id(user_id):
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()
        return dict(user) if user else None

class Tag:
    @staticmethod
    def create(user_id, name, is_public=False):
        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO tags (user_id, name, is_public) VALUES (?, ?, ?)',
                (user_id, name, is_public)
            )
            conn.commit()
            return conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        finally:
            conn.close()
    
    @staticmethod
    def get_by_user(user_id):
        conn = get_db_connection()
        tags = conn.execute(
            'SELECT * FROM tags WHERE user_id = ? ORDER BY name', 
            (user_id,)
        ).fetchall()
        conn.close()
        return [dict(tag) for tag in tags]
    
    @staticmethod
    def get_public_tags():
        conn = get_db_connection()
        tags = conn.execute(
            'SELECT t.*, u.username FROM tags t JOIN users u ON t.user_id = u.id WHERE t.is_public = 1'
        ).fetchall()
        conn.close()
        return [dict(tag) for tag in tags]
    
    @staticmethod
    def update_visibility(tag_id, user_id, is_public):
        conn = get_db_connection()
        try:
            # Update tag visibility
            conn.execute(
                'UPDATE tags SET is_public = ? WHERE id = ? AND user_id = ?',
                (is_public, tag_id, user_id)
            )
            
            # Update all flashcards under this tag if making public
            if is_public:
                conn.execute(
                    'UPDATE flashcards SET is_public = 1 WHERE tag_id = ? AND user_id = ?',
                    (tag_id, user_id)
                )
            conn.commit()
            return True
        finally:
            conn.close()

class Flashcard:
    @staticmethod
    def create(user_id, tag_id, question, options, correct_answer, is_public):
        conn = get_db_connection()
        conn.execute(
            '''
            INSERT INTO flashcards (user_id, tag_id, question, options, correct_answer, is_public)
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (user_id, tag_id, question, json.dumps(options), correct_answer, is_public)
        )
        conn.commit()
        conn.close()




    
    @staticmethod
    def get_by_tag(tag_id, user_id=None):
        conn = get_db_connection()
        query = '''
            SELECT * FROM flashcards 
            WHERE tag_id = ? AND (user_id = ? OR is_public = 1)
        '''
        flashcards = conn.execute(query, (tag_id, user_id)).fetchall()
        conn.close()
        
        result = []
        for card in flashcards:
            card_dict = dict(card)
            card_dict['options'] = json.loads(card_dict['options'])
            result.append(card_dict)
        return result
    
    @staticmethod
    def update_review_schedule(flashcard_id, user_id, is_correct):
        conn = get_db_connection()
        now = datetime.datetime.now()
        
        # Get current review count
        card = conn.execute(
            'SELECT review_count FROM flashcards WHERE id = ? AND user_id = ?',
            (flashcard_id, user_id)
        ).fetchone()
        
        if not card:
            conn.close()
            return False
        
        review_count = card['review_count'] + 1
        
        # Calculate next review time based on spaced repetition algorithm
        # Simple implementation: double the interval each time if correct, reset if wrong
        if is_correct:
            # 1 day, 2 days, 4 days, 8 days, etc.
            interval = 24 * (2 ** (review_count - 1))  # hours
        else:
            interval = 6  # 6 hours if wrong
            review_count = 1  # Reset review count if wrong
        
        next_review = now + datetime.timedelta(hours=interval)
        
        # Update the flashcard
        conn.execute(
            '''UPDATE flashcards 
               SET last_reviewed = ?, next_review = ?, review_count = ?
               WHERE id = ? AND user_id = ?''',
            (now.isoformat(), next_review.isoformat(), review_count, flashcard_id, user_id)
        )
        
        # Record progress
        conn.execute(
            'INSERT INTO user_progress (user_id, flashcard_id, is_correct) VALUES (?, ?, ?)',
            (user_id, flashcard_id, is_correct)
        )
        
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def get_due_for_review(user_id):
        conn = get_db_connection()
        now = datetime.datetime.now().isoformat()
        
        cards = conn.execute(
            '''SELECT * FROM flashcards 
               WHERE user_id = ? AND (next_review IS NULL OR next_review <= ?)
               ORDER BY RANDOM() LIMIT 10''',
            (user_id, now)
        ).fetchall()
        
        conn.close()
        
        result = []
        for card in cards:
            card_dict = dict(card)
            card_dict['options'] = json.loads(card_dict['options'])
            result.append(card_dict)
        return result

class Progress:
    @staticmethod
    def get_user_stats(user_id):
        conn = get_db_connection()
        
        stats = {}
        
        # Total flashcards created
        total_cards = conn.execute(
            'SELECT COUNT(*) as count FROM flashcards WHERE user_id = ?', 
            (user_id,)
        ).fetchone()['count']
        stats['total_cards'] = total_cards
        
        # Total attempts
        total_attempts = conn.execute(
            'SELECT COUNT(*) as count FROM user_progress WHERE user_id = ?', 
            (user_id,)
        ).fetchone()['count']
        stats['total_attempts'] = total_attempts
        
        # Success rate
        if total_attempts > 0:
            correct_attempts = conn.execute(
                'SELECT COUNT(*) as count FROM user_progress WHERE user_id = ? AND is_correct = 1', 
                (user_id,)
            ).fetchone()['count']
            stats['success_rate'] = round((correct_attempts / total_attempts) * 100, 2)
        else:
            stats['success_rate'] = 0
        
        # Cards due for review
        now = datetime.datetime.now().isoformat()
        due_cards = conn.execute(
            '''SELECT COUNT(*) as count FROM flashcards 
               WHERE user_id = ? AND (next_review IS NULL OR next_review <= ?)''',
            (user_id, now)
        ).fetchone()['count']
        stats['due_cards'] = due_cards
        
        # Cards by tag
        tag_stats = conn.execute(
            '''SELECT t.name, COUNT(f.id) as card_count
               FROM tags t
               LEFT JOIN flashcards f ON t.id = f.tag_id
               WHERE t.user_id = ?
               GROUP BY t.id''',
            (user_id,)
        ).fetchall()
        stats['tags'] = [dict(tag) for tag in tag_stats]
        
        conn.close()
        return stats

class Notification:
    @staticmethod
    def create(user_id, message, scheduled_for=None):
        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO notifications (user_id, message, scheduled_for) VALUES (?, ?, ?)',
                (user_id, message, scheduled_for)
            )
            conn.commit()
            return True
        finally:
            conn.close()
    
    @staticmethod
    def get_unread(user_id):
        conn = get_db_connection()
        now = datetime.datetime.now().isoformat()
        
        notifications = conn.execute(
            '''SELECT * FROM notifications 
               WHERE user_id = ? AND is_read = 0 
               AND (scheduled_for IS NULL OR scheduled_for <= ?)
               ORDER BY created_at DESC''',
            (user_id, now)
        ).fetchall()
        
        conn.close()
        return [dict(notification) for notification in notifications]
    
    @staticmethod
    def mark_as_read(notification_id, user_id):
        conn = get_db_connection()
        try:
            conn.execute(
                'UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?',
                (notification_id, user_id)
            )
            conn.commit()
            return True
        finally:
            conn.close()

class Reward:
    @staticmethod
    def grant(user_id, name, description=None):
        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO rewards (user_id, name, description) VALUES (?, ?, ?)',
                (user_id, name, description)
            )
            conn.commit()
            return True
        finally:
            conn.close()
    
    @staticmethod
    def get_user_rewards(user_id):
        conn = get_db_connection()
        rewards = conn.execute(
            'SELECT * FROM rewards WHERE user_id = ? ORDER BY achieved_at DESC',
            (user_id,)
        ).fetchall()
        conn.close()
        return [dict(reward) for reward in rewards]
