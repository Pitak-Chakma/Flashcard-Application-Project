import sqlite3
import json
from werkzeug.security import generate_password_hash

# Connect to the database
DATABASE = 'flashcards.db'  # Update this if your database file has a different name
conn = sqlite3.connect(DATABASE)

# Create a cursor object
cursor = conn.cursor()

# Insert a dummy user
def insert_dummy_user():
    username = "testuser"
    email = "testuser@example.com"
    password = "Test@1234"
    password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    cursor.execute(
        '''
        INSERT INTO users (username, email, password_hash)
        VALUES (?, ?, ?)
        ''',
        (username, email, password_hash)
    )
    user_id = cursor.lastrowid
    print(f"Inserted dummy user with ID: {user_id}")
    return user_id

# Insert dummy tags
def insert_dummy_tags(user_id):
    tags = [
        {"name": "Math", "is_public": 1},
        {"name": "Science", "is_public": 0},
        {"name": "History", "is_public": 1},
    ]
    tag_ids = []
    for tag in tags:
        cursor.execute(
            '''
            INSERT INTO tags (user_id, name, is_public)
            VALUES (?, ?, ?)
            ''',
            (user_id, tag["name"], tag["is_public"])
        )
        tag_ids.append(cursor.lastrowid)
    print(f"Inserted dummy tags with IDs: {tag_ids}")
    return tag_ids

# Insert dummy flashcards
def insert_dummy_flashcards(user_id, tag_ids):
    flashcards = [
        {
            "tag_id": tag_ids[0],
            "question": "What is 2 + 2?",
            "options": json.dumps(["3", "4", "5", "6"]),
            "correct_answer": "4",
            "is_public": 1,
        },
        {
            "tag_id": tag_ids[1],
            "question": "What is the chemical symbol for water?",
            "options": json.dumps(["H2O", "O2", "CO2", "HO"]),
            "correct_answer": "H2O",
            "is_public": 0,
        },
        {
            "tag_id": tag_ids[2],
            "question": "Who was the first president of the United States?",
            "options": json.dumps(["Abraham Lincoln", "George Washington", "Thomas Jefferson", "John Adams"]),
            "correct_answer": "George Washington",
            "is_public": 1,
        },
    ]
    flashcard_ids = []
    for card in flashcards:
        cursor.execute(
            '''
            INSERT INTO flashcards (user_id, tag_id, question, options, correct_answer, is_public)
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (user_id, card["tag_id"], card["question"], card["options"], card["correct_answer"], card["is_public"])
        )
        flashcard_ids.append(cursor.lastrowid)
    print(f"Inserted dummy flashcards with IDs: {flashcard_ids}")
    return flashcard_ids

# Insert dummy progress
def insert_dummy_progress(user_id, flashcard_ids):
    progress = [
        {"flashcard_id": flashcard_ids[0], "is_correct": 1},
        {"flashcard_id": flashcard_ids[1], "is_correct": 0},
        {"flashcard_id": flashcard_ids[2], "is_correct": 1},
    ]
    for entry in progress:
        cursor.execute(
            '''
            INSERT INTO user_progress (user_id, flashcard_id, is_correct)
            VALUES (?, ?, ?)
            ''',
            (user_id, entry["flashcard_id"], entry["is_correct"])
        )
    print("Inserted dummy progress data.")

# Main function to populate dummy data
def populate_dummy_data():
    print("Populating dummy data...")
    user_id = insert_dummy_user()
    tag_ids = insert_dummy_tags(user_id)
    flashcard_ids = insert_dummy_flashcards(user_id, tag_ids)
    insert_dummy_progress(user_id, flashcard_ids)
    conn.commit()
    print("Dummy data populated successfully!")

# Run the script
if __name__ == "__main__":
    populate_dummy_data()
    conn.close()
