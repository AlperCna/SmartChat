# backend/app.py

from flask import Flask, jsonify, request
from backend.services import db_service
from flask_cors import CORS

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # Türkçe karakter sorununu önler

CORS(app)  # Frontend'in API'ye erişmesini sağlar alpor

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


# Ana çalışma bloğu
if __name__ == "__main__":
    app.run(debug=True)