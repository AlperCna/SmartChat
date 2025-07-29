import mysql.connector

# Veritabanı bağlantısı fonksiyonu
def get_db_connection():
    conn = mysql.connector.connect(
        host="localhost",        # AWS RDS'e geçince burası değişecek
        user="root",             # MySQL kullanıcı adın
        password="bc748596", # MySQL şifren
        database="smartchat"
    )
    return conn

# Kullanıcı ekleme
def insert_user(username, email, password_hash):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)"
    cursor.execute(sql, (username, email, password_hash))
    conn.commit()
    cursor.close()
    conn.close()

# Tüm kullanıcıları listeleme
def get_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return users


# Yeni mesaj ekle
def insert_message(sender_id, receiver_id, content):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO messages (sender_id, receiver_id, content) VALUES (%s, %s, %s)"
    cursor.execute(sql, (sender_id, receiver_id, content))
    conn.commit()
    cursor.close()
    conn.close()

# İki kullanıcı arasındaki mesajları listeleme
def get_messages(sender_id, receiver_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    sql = """
        SELECT * FROM messages
        WHERE (sender_id = %s AND receiver_id = %s)
           OR (sender_id = %s AND receiver_id = %s)
        ORDER BY timestamp ASC
    """
    cursor.execute(sql, (sender_id, receiver_id, receiver_id, sender_id))
    messages = cursor.fetchall()
    cursor.close()
    conn.close()
    return messages





