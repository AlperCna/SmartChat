from backend.services.db_service import get_db_connection

def main():
    try:
        conn = get_db_connection()
        if conn.is_connected():
            print("✅ Veritabanına bağlantı başarılı!")
        else:
            print("❌ Bağlantı kusulamadı.")
    except Exception as e:
        print(f"❌ Bağlantı hatası: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()

if __name__ == "__main__":
    main()