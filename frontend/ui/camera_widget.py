from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer
import cv2
import requests
import os
from datetime import datetime

class CameraWidget(QWidget):
    def __init__(self, sender_id, receiver_id):
        super().__init__()
        self.sender_id = sender_id
        self.receiver_id = receiver_id

        self.setWindowTitle("📷 Kamera")
        self.setFixedSize(640, 520)
        self.setStyleSheet("background-color: #121212; color: white; font-family: 'Segoe UI';")

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.image_label = QLabel("Kamera başlatılıyor...")
        self.image_label.setFixedSize(640, 480)
        self.image_label.setStyleSheet("background-color: black;")
        self.layout.addWidget(self.image_label)

        self.capture_button = QPushButton("📸 Fotoğraf Çek ve Gönder")
        self.layout.addWidget(self.capture_button)

        self.capture_button.clicked.connect(self.capture_and_upload)

        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
            self.image_label.setPixmap(QPixmap.fromImage(image))

    def capture_and_upload(self):
        ret, frame = self.cap.read()
        if not ret:
            QMessageBox.critical(self, "Hata", "Kamera görüntüsü alınamadı.")
            return

        # 📂 Benzersiz dosya adı oluştur
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"photo_{timestamp}.jpg"
        docs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "docs"))
        os.makedirs(docs_path, exist_ok=True)
        full_path = os.path.join(docs_path, filename)
        cv2.imwrite(full_path, frame)

        try:
            # 1️⃣ Önce mesaj oluştur
            msg_response = requests.post("http://127.0.0.1:5000/messages", json={
                "sender_id": self.sender_id,
                "receiver_id": self.receiver_id,
                "content": "[📷 Fotoğraf]"
            })

            if msg_response.status_code != 200:
                raise Exception("Mesaj oluşturulamadı.")

            message_id = msg_response.json().get("message_id")
            if not message_id:
                raise Exception("message_id alınamadı")

            # 2️⃣ Fotoğrafı yükle
            with open(full_path, "rb") as f:
                upload_response = requests.post("http://127.0.0.1:5000/upload_media", files={
                    "file": (filename, f, "image/jpeg")
                }, data={
                    "media_type": "image",
                    "message_id": str(message_id)  # ✅ string olarak gönderildi
                })

            if upload_response.status_code == 200:
                QMessageBox.information(self, "Başarılı", "📤 Fotoğraf başarıyla gönderildi!")
                self.close()
            else:
                raise Exception(upload_response.text)

        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def closeEvent(self, event):
        self.timer.stop()
        self.cap.release()
        super().closeEvent(event)
