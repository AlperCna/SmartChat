# backend/app.py

from flask import Flask, jsonify, request
from backend.services import db_service
from flask_cors import CORS
import bcrypt

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # Türkçe karakter sorununu önler

CORS(app)  # Frontend'in API'ye erişmesini sağlar deneme123

# Test endpoint'i
@app.route("/hello", methods=["GET"])
def hello():
    return {"message": "SmartChat Flask sunucusu çalışıyor."}

# Kullanıcıları listeleme (GET)
@app.route("/users", methods=["GET"])
def list_users():
    return jsonify(db_service.get_users())

# Kullanıcı oluşturma (POST)
@app.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password_hash = data.get("password_hash")  # ⬅️ EKLENDİ

    # Hepsi zorunlu
    if not username or not email or not password_hash:
        return jsonify({"error": "username, email ve password_hash zorunludur."}), 400

    db_service.insert_user(username, email, password_hash)  # ⬅️ Güncellendi
    return jsonify({"message": "Kullanıcı başarıyla ekle."})


# Mesaj gönderme (POST)
@app.route("/messages", methods=["POST"])
def send_message():
    data = request.get_json()
    sender_id = data.get("sender_id")
    receiver_id = data.get("receiver_id")
    content = data.get("content")

    if not sender_id or not receiver_id or not content:
        return jsonify({"error": "sender_id, receiver_id ve content zorunludur."}), 400

    db_service.insert_message(sender_id, receiver_id, content)
    return jsonify({"message": "Mesaj başarıyla gönderildi."})

# Mesajları listeleme (GET)
@app.route("/messages", methods=["GET"])
def list_messages():
    sender_id = request.args.get("sender_id")
    receiver_id = request.args.get("receiver_id")

    if not sender_id or not receiver_id:
        return jsonify({"error": "sender_id ve receiver_id zorunludur."}), 400

    messages = db_service.get_messages(sender_id, receiver_id)
    return jsonify(messages)

@app.route("/signup", methods=["POST"])
def signup():
    try:
        data = request.get_json()
        username = data.get("username", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "")

        # 1️⃣ Validate input
        if not username or not email or not password:
            return jsonify({"error": "All fields are required"}), 400

        # 2️⃣ Check if email already exists
        existing_user = db_service.get_user_by_email(email)
        if existing_user:
            return jsonify({"error": "Email is already registered"}), 409

        # 3️⃣ Check if username already exists
        existing_username = db_service.get_user_by_username(username)
        if existing_username:
            return jsonify({"error": "Username is already taken"}), 409

        # 4️⃣ Hash password with bcrypt
        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        # 5️⃣ Insert into DB
        db_service.insert_user(username, email, hashed_pw)

        return jsonify({"message": "User created successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        email = data.get("email", "").strip()
        password = data.get("password", "")

        # Find user
        user = db_service.get_user_by_email(email)
        if not user:
            return jsonify({"success": False, "error": "User not found"}), 401

        stored_pw = user["password_hash"]
        if not stored_pw or not stored_pw.startswith("$2"):  # bcrypt hashes always start with $2
            return jsonify({"success": False, "error": "Invalid password hash format"}), 500

        # Check password
        if not bcrypt.checkpw(password.encode("utf-8"), stored_pw.encode("utf-8")):
            return jsonify({"success": False, "error": "Invalid password"}), 401

        return jsonify({"success": True, "user_id": user["user_id"]}), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500





# Ana çalışma bloğu
if __name__ == "__main__":
    app.run(debug=True)