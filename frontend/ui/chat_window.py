from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QLabel, QLineEdit, QMessageBox, QListWidgetItem, QDialog, QTextEdit, QScrollArea, QSizePolicy
from PyQt5.QtCore import Qt, QTimer
import requests
from datetime import datetime


class ChatWindow(QWidget):
    def __init__(self, sender_id, sender_username, receiver_id, receiver_username):
        super().__init__()
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.sender_username = sender_username
        self.receiver_username = receiver_username

        self.setMinimumSize(400, 500)
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Segoe UI';
                font-size: 14px;
            }
            QLineEdit {
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

        self.title_label = QLabel(f"\U0001F4AC Konusma: {self.receiver_username}")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.title_label)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.message_container = QWidget()
        self.message_layout = QVBoxLayout()
        self.message_layout.setAlignment(Qt.AlignTop)
        self.message_container.setLayout(self.message_layout)
        self.scroll.setWidget(self.message_container)

        self.layout.addWidget(self.scroll)

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Mesaj yazin...")
        self.send_button = QPushButton("Gonder")

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)
        self.layout.addLayout(input_layout)

        self.send_button.clicked.connect(self.send_message)
        self.message_input.returnPressed.connect(self.send_message)

        self.load_messages()
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_messages)
        self.timer.start(3000)

    def add_message_label(self, text, sender, timestamp):
        time_text = "--:--"
        try:
            time_text = datetime.fromisoformat(timestamp).strftime("%H:%M") if timestamp else "--:--"
        except:
            pass

        header = QLabel(f"{sender}  \u23F0 {time_text}")
        header.setStyleSheet("color: #ccc; font-size: 11px; padding-bottom: 2px;")

        body = QLabel(text)
        body.setWordWrap(True)
        body.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        body.setMaximumWidth(400)
        body.setStyleSheet(f"""
            background-color: {'#3a87f2' if sender == self.sender_username else '#2c2c2c'};
            color: white;
            border-radius: 10px;
            padding: 8px 12px;
        """)

        wrapper = QWidget()
        wrapper_layout = QVBoxLayout()
        wrapper_layout.setContentsMargins(10, 5, 10, 5)
        wrapper_layout.setSpacing(0)
        wrapper.setLayout(wrapper_layout)
        wrapper_layout.addWidget(header)
        wrapper_layout.addWidget(body)

        align_wrapper = QWidget()
        align_layout = QHBoxLayout()
        align_layout.setContentsMargins(0, 0, 0, 0)
        align_wrapper.setLayout(align_layout)

        if sender == self.sender_username:
            align_layout.addStretch()
            align_layout.addWidget(wrapper)
        else:
            align_layout.addWidget(wrapper)
            align_layout.addStretch()

        self.message_layout.addWidget(align_wrapper)

    def load_messages(self):
        try:
            url = f"http://127.0.0.1:5000/messages?sender_id={self.sender_id}&receiver_id={self.receiver_id}"
            response = requests.get(url)
            if response.status_code == 200:
                messages = response.json()
                for i in reversed(range(self.message_layout.count())):
                    item = self.message_layout.itemAt(i)
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
                for msg in messages:
                    sender_name = self.sender_username if msg["sender_id"] == self.sender_id else self.receiver_username
                    self.add_message_label(msg["content"], sender_name, msg.get("timestamp"))
                self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())
        except Exception as e:
            self.add_message_label(f"Hata: {e}", "Sistem", None)

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
            self.add_message_label(f"Gonderim hatasi: {e}", "Sistem", None)
