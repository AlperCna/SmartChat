import bcrypt
import mysql.connector

def get_db_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="bc748596",
        database="smartchat"
    )
    return conn

def insert_user(username, email, password_hash):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)"
    cursor.execute(sql, (username, email, password_hash))
    conn.commit()
    cursor.close()
    conn.close()

def get_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return users

def insert_message(sender_id, receiver_id, content):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO messages (sender_id, receiver_id, content) VALUES (%s, %s, %s)"
    cursor.execute(sql, (sender_id, receiver_id, content))
    message_id = cursor.lastrowid  # ✅ eklendi
    conn.commit()
    cursor.close()
    conn.close()
    return message_id  # ✅ döndürülüyor

def get_messages(sender_id, receiver_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    sql = """
        SELECT m.*, media.file_path, media.media_type
        FROM messages m
        LEFT JOIN media ON m.message_id = media.message_id
        WHERE (m.sender_id = %s AND m.receiver_id = %s)
           OR (m.sender_id = %s AND m.receiver_id = %s)
        ORDER BY m.timestamp ASC
    """
    cursor.execute(sql, (sender_id, receiver_id, receiver_id, sender_id))
    messages = cursor.fetchall()
    cursor.close()
    conn.close()
    return messages

def get_user_by_email(email):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def get_user_by_username(username):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def get_chat_partners(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT DISTINCT u.user_id, u.username
        FROM users u
        JOIN messages m ON (u.user_id = m.sender_id OR u.user_id = m.receiver_id)
        WHERE %s IN (m.sender_id, m.receiver_id) AND u.user_id != %s
    """, (user_id, user_id))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

def insert_media(message_id, media_type, file_path):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = """
        INSERT INTO media (message_id, media_type, file_path, uploaded_at)
        VALUES (%s, %s, %s, NOW())
    """
    cursor.execute(sql, (message_id, media_type, file_path))
    conn.commit()
    cursor.close()
    conn.close()
