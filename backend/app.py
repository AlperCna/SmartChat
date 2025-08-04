from flask import Flask, jsonify, request
from backend.services import db_service
from flask_cors import CORS
import bcrypt
import os
from werkzeug.utils import secure_filename
from ai_module.spell_corrector import correct_spelling
from ai_module.punctuation_fixer import suggest_punctuation

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
CORS(app)

# 📂 Medya dosyalarının kaydedileceği klasör
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "..", "docs")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/hello", methods=["GET"])
def hello():
    return {"message": "SmartChat Flask sunucusu çalışıyor."}

@app.route("/users", methods=["GET"])
def list_users():
    return jsonify(db_service.get_users())

@app.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password_hash = data.get("password_hash")
    if not username or not email or not password_hash:
        return jsonify({"error": "username, email ve password_hash zorunludur."}), 400
    db_service.insert_user(username, email, password_hash)
    return jsonify({"message": "Kullanıcı başarıyla eklendi."})

@app.route("/messages", methods=["POST"])
def send_message():
    data = request.get_json()
    sender_id = data.get("sender_id")
    receiver_id = data.get("receiver_id")
    content = data.get("content")
    if not sender_id or not receiver_id or not content:
        return jsonify({"error": "sender_id, receiver_id ve content zorunludur."}), 400

    message_id = db_service.insert_message(sender_id, receiver_id, content)
    return jsonify({
        "message": "Mesaj başarıyla gönderildi.",
        "message_id": message_id
    }), 200


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
        if not username or not email or not password:
            return jsonify({"error": "All fields are required"}), 400
        if db_service.get_user_by_email(email):
            return jsonify({"error": "Email is already registered"}), 409
        if db_service.get_user_by_username(username):
            return jsonify({"error": "Username is already taken"}), 409
        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
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
        user = db_service.get_user_by_email(email)
        if not user:
            return jsonify({"success": False, "error": "User not found"}), 401
        stored_pw = user["password_hash"]
        if not stored_pw or not stored_pw.startswith("$2"):
            return jsonify({"success": False, "error": "Invalid password hash format"}), 500
        if not bcrypt.checkpw(password.encode("utf-8"), stored_pw.encode("utf-8")):
            return jsonify({"success": False, "error": "Invalid password"}), 401
        return jsonify({"success": True, "user_id": user["user_id"]}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/user_by_username/<username>", methods=["GET"])
def get_user_by_username(username):
    user = db_service.get_user_by_username(username)
    if user:
        return jsonify(user)
    return jsonify({"error": "User not found"}), 404

@app.route("/user_by_id/<int:user_id>", methods=["GET"])
def get_user_by_id(user_id):
    user = db_service.get_user_by_id(user_id)
    if user:
        return jsonify(user)
    return jsonify({"error": "User not found"}), 404

@app.route("/chat_partners/<int:user_id>", methods=["GET"])
def chat_partners(user_id):
    return jsonify(db_service.get_chat_partners(user_id))

# 📤 Yeni: Fotoğraf/ses/video medya dosyası yükleme
@app.route("/upload_media", methods=["POST"])
def upload_media():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    media_type = request.form.get("media_type", "image")
    message_id = request.form.get("message_id")  # opsiyonel olabilir

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(save_path)

    # veritabanına kayıt
    db_service.insert_media(message_id, media_type, f"docs/{filename}")

    return jsonify({"message": "Media uploaded", "file_path": f"docs/{filename}"})


@app.route("/suggest", methods=["POST"])
def suggest_text():
    try:
        data = request.get_json()
        text = data.get("text", "").strip()
        user_id = data.get("user_id")

        if not text or not user_id:
            return jsonify({"error": "text ve user_id zorunludur"}), 400

        corrected = correct_spelling(text)
        punctuated = suggest_punctuation(corrected)

        suggestion_id = db_service.insert_suggestion(user_id, text, punctuated)

        return jsonify({
            "suggestion_id": suggestion_id,
            "original": text,
            "corrected": corrected,
            "punctuated": punctuated
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/suggestions/<int:suggestion_id>", methods=["PATCH"])
def update_suggestion(suggestion_id):
    try:
        data = request.get_json()
        accepted = data.get("accepted")

        if accepted not in [True, False]:
            return jsonify({"error": "accepted alanı true/false olmalı"}), 400

        db_service.update_suggestion_acceptance(suggestion_id, accepted)
        return jsonify({"message": "Kabul durumu güncellendi"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
