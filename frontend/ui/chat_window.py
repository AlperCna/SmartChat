from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QTextEdit, QLabel, QScrollArea, QHBoxLayout
from PyQt5.QtCore import QTimer, Qt
import requests

class ChatWindow(QWidget):
    def __init__(self, sender_id, receiver_id):
        super().__init__()
        self.sender_id = sender_id
        self.receiver_id = receiver_id

        self.setWindowTitle(f"💬 SmartChat — Kullanıcı {self.sender_id}")
        self.setMinimumSize(400, 500)
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Segoe UI';
                font-size: 14px;
            }
            QTextEdit, QLineEdit {
                background-color: #2c2c2c;
                border: 1px solid #444;
                border-radius: 10px;
                padding: 6px;
                color: white;
            }
            QPushButton {
                background-color: #3a87f2;
                color: white;
                border-radius: 10px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #5c9dff;
            }
        """)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Scrollable mesaj alanı
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.message_container = QWidget()
        self.message_layout = QVBoxLayout()
        self.message_container.setLayout(self.message_layout)
        self.scroll.setWidget(self.message_container)

        # Mesaj giriş alanı
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Mesaj yazın...")
        self.send_button = QPushButton("Gönder")

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)

        self.layout.addWidget(self.scroll)
        self.layout.addLayout(input_layout)

        self.send_button.clicked.connect(self.send_message)
        self.message_input.returnPressed.connect(self.send_message)

        # İlk mesajlar
        self.load_messages()

        # Otomatik yenileme
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_messages)
        self.timer.start(3000)

    def add_message_label(self, text, sender):
        label = QLabel(f"{sender}: {text}")
        label.setWordWrap(True)
        label.setStyleSheet(f"""
            background-color: {'#3a87f2' if sender == str(self.sender_id) else '#444'};
            border-radius: 10px;
            padding: 6px 10px;
            margin: 4px;
            max-width: 300px;
        """)
        alignment = Qt.AlignRight if sender == str(self.sender_id) else Qt.AlignLeft
        label.setAlignment(alignment)
        self.message_layout.addWidget(label, alignment)

    def load_messages(self):
        try:
            url = f"http://127.0.0.1:5000/messages?sender_id={self.sender_id}&receiver_id={self.receiver_id}"
            response = requests.get(url)
            if response.status_code == 200:
                messages = response.json()
                # Önce tüm mesajları temizle
                for i in reversed(range(self.message_layout.count())):
                    self.message_layout.itemAt(i).widget().deleteLater()
                # Yeni mesajları ekle
                for msg in messages:
                    self.add_message_label(msg["content"], str(msg["sender_id"]))
                self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())
        except Exception as e:
            self.add_message_label(f"Hata: {e}", "Sistem")

    def send_message(self):
        content = self.message_input.text().strip()
        if not content:
            return

        data = {
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "content": content
        }

        try:
            url = "http://127.0.0.1:5000/messages"
            response = requests.post(url, json=data)
            if response.status_code == 200:
                self.message_input.clear()
                self.load_messages()
        except Exception as e:
            self.add_message_label(f"Gönderim hatası: {e}", "Sistem")
