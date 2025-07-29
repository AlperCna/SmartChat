import requests

def post_user():
    url = "http://127.0.0.1:5000/users"
    data = {
        "username": "pythontest",
        "email": "python@example.com",
        "password_hash": "abc123"
    }

    try:
        response = requests.post(url, json=data)
        print("🔄 Durum:", response.status_code)
        print("📬 Cevap:", response.json())
    except Exception as e:
        print("❌ Hata:", e)

if __name__ == "__main__":
    post_user()
