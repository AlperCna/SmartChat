from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox
import sounddevice as sd
from scipy.io.wavfile import write
import os
from datetime import datetime
import requests

class MicWidget(QWidget):
    def __init__(self, sender_id, receiver_id):
        super().__init__()
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.fs = 44100  # Sampling rate
        self.duration = 5  # seconds

        self.setWindowTitle("🎙️ Ses Kaydı")
        self.setFixedSize(400, 150)
        self.setStyleSheet("background-color: #121212; color: white; font-family: 'Segoe UI';")

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.label = QLabel("🎤 5 saniyelik ses kaydı yapılacak.")
        layout.addWidget(self.label)

        self.record_button = QPushButton("🎙️ Kaydı Başlat ve Gönder")
        layout.addWidget(self.record_button)
        self.record_button.clicked.connect(self.record_audio)

    def record_audio(self):
        try:
            self.label.setText("🎙️ Kayıt yapılıyor...")
            audio = sd.rec(int(self.duration * self.fs), samplerate=self.fs, channels=1, dtype='int16')
            sd.wait()

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"audio_{timestamp}.wav"
            docs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "docs"))
            os.makedirs(docs_path, exist_ok=True)
            full_path = os.path.join(docs_path, filename)
            write(full_path, self.fs, audio)

            # 1️⃣ Mesaj oluştur
            msg_response = requests.post("http://127.0.0.1:5000/messages", json={
                "sender_id": self.sender_id,
                "receiver_id": self.receiver_id,
                "content": "[🎧 Ses]"
            })

            if msg_response.status_code != 200:
                raise Exception("Mesaj oluşturulamadı")

            message_id = msg_response.json().get("message_id")
            if not message_id:
                raise Exception("message_id alınamadı")

            # 2️⃣ Dosyayı yükle
            with open(full_path, "rb") as f:
                upload_response = requests.post("http://127.0.0.1:5000/upload_media", files={
                    "file": (filename, f, "audio/wav")
                }, data={
                    "media_type": "audio",
                    "message_id": str(message_id)
                })

            if upload_response.status_code == 200:
                QMessageBox.information(self, "Başarılı", "🎧 Ses kaydı gönderildi.")
                self.close()
            else:
                raise Exception(upload_response.text)

        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
