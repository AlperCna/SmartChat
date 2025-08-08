from flask import Flask, jsonify, request
from backend.services import db_service
from flask_cors import CORS
import bcrypt
import os
from werkzeug.utils import secure_filename
from ai_module.spell_corrector import correct_spelling
from ai_module.punctuation_fixer import suggest_punctuation
from ai_module.style_adapter import detect_style, adapt_style
from openai import OpenAI
from dotenv import load_dotenv
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Load environment and initialize
analyzer = SentimentIntensityAnalyzer()
load_dotenv()
print("API Key test:", os.getenv("OPENAI_API_KEY")[:6], "...")  # show only first 6 chars
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize Flask
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
CORS(app)

# Media upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "..", "docs")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Health check route (for browser testing)
@app.route("/", methods=["GET"])
def index():
    return {"message": "SmartChat Flask backend is alive!"}

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

@app.route("/upload_media", methods=["POST"])
def upload_media():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    media_type = request.form.get("media_type", "image")
    message_id = request.form.get("message_id")
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    filename = secure_filename(file.filename)
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(save_path)
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

@app.route("/complete", methods=["POST"])
def complete_text():
    try:
        print(">>> /complete endpoint called")
        data = request.get_json()
        print("[INPUT] JSON received:", data)

        text = data.get("text", "").strip()
        receiver_username = data.get("receiver_username", "")
        sender_id = data.get("sender_id")
        receiver_id = data.get("receiver_id")

        print(f"[INPUT] text='{text}', receiver_username='{receiver_username}', sender_id={sender_id}, receiver_id={receiver_id}")

        if not text or not sender_id or not receiver_id:
            print("[ERROR] Missing parameters")
            return jsonify({"error": "text, sender_id ve receiver_id zorunludur"}), 400

        # Fetch last 5 messages for conversation context
        messages = db_service.get_messages(sender_id, receiver_id)
        print(f"[DB] Retrieved {len(messages)} messages from db")
        last_msgs = messages[-5:]

        # Build prompt history
        history = ""
        for m in last_msgs:
            speaker = "Me" if m["sender_id"] == sender_id else receiver_username
            history += f"{speaker}: {m['content']}\n"

        # Detect style
        style = detect_style(sender_id, receiver_id, last_message=text)
        print(f"[STYLE] Detected style: {style}")

        # Analyze sentiment
        sentiment_prompt = f"""
        Mesaj: "{text}"
        Görev: Bu mesajın duygusunu sınıflandır.
        Sadece 'positive', 'negative' veya 'neutral' olarak cevap ver.
        """
        print(f"[GPT] Sentiment prompt:\n{sentiment_prompt}")

        sentiment_res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": sentiment_prompt}],
            max_tokens=3
        )
        sentiment = sentiment_res.choices[0].message.content.strip().lower()
        print(f"[SENTIMENT] Result: {sentiment}")

        # Adjust closeness
        delta = 0
        if sentiment == "positive":
            delta = 5
        elif sentiment == "negative":
            delta = -5

        if delta != 0:
            db_service.adjust_closeness(sender_id, receiver_id, delta)
            print(f"[CLOSENESS] Adjusted by {delta} based on sentiment")

        # Build final completion prompt
        prompt = f"""
        Görev: Aşağıdaki konuşma geçmişine göre, kullanıcının son mesajını yazım hatalarını düzelterek ve '{style}' üsluba uyarlayarak tamamla.
        Konuşma geçmişi:
        {history}
        Kullanıcının son mesajı: {text}
        """
        print(f"[GPT] Completion prompt:\n{prompt}")

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50
        )

        completion_text = response.choices[0].message.content.strip()
        print(f"[COMPLETION] Generated: {completion_text}")

        # Save suggestion to DB
        suggestion_id = db_service.insert_suggestion(sender_id, text, completion_text, style)
        print(f"[DB] Suggestion saved with ID: {suggestion_id}")

        return jsonify({
            "suggestion_id": suggestion_id,
            "original": text,
            "completion": completion_text,
            "style": style,
            "styled_completion": completion_text,
            "sentiment": sentiment
        })

    except Exception as e:
        import traceback
        print("[ERROR] Exception occurred in /complete:", str(e))
        traceback.print_exc()
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

# 🔥 Run the app only if executed directly (not when imported by Gunicorn)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
