from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QLabel, QLineEdit, QMessageBox, QListWidgetItem, QDialog
from PyQt5.QtCore import Qt
from .chat_window import ChatWindow
import requests


class ChatPanelWindow(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.sender_username = ""
        self.setWindowTitle("💬 SmartChat — Sohbetler")
        self.setMinimumSize(900, 600)
        self.setStyleSheet("""
            QWidget {
                background-color: #121212;
                color: #ffffff;
                font-family: 'Segoe UI';
                font-size: 14px;
            }
            QListWidget {
                background-color: #1e1e1e;
                border: none;
                padding: 5px;
            }
            QListWidget::item {
                padding: 10px;
                margin: 4px;
                border-radius: 6px;
            }
            QListWidget::item:selected {
                background-color: #3a87f2;
                color: white;
            }
            QPushButton {
                background-color: #3a87f2;
                color: white;
                border-radius: 10px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #5c9dff;
            }
            QLabel {
                padding: 4px;
            }
        """)

        self.active_chat = None

        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        left_panel = QVBoxLayout()
        self.username_label = QLabel("👤")
        self.username_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")

        self.chat_list = QListWidget()
        self.chat_list.setSpacing(6)

        self.new_chat_btn = QPushButton("➕ Yeni Sohbet")
        self.new_chat_btn.clicked.connect(self.new_chat)

        left_panel.addWidget(self.username_label)
        left_panel.addWidget(self.chat_list)
        left_panel.addWidget(self.new_chat_btn)

        self.chat_area = QVBoxLayout()
        self.chat_placeholder = QLabel("💬 Sağda sohbet penceresi görünecek.")
        self.chat_placeholder.setAlignment(Qt.AlignCenter)
        self.chat_placeholder.setStyleSheet("color: #888; font-size: 16px;")
        self.chat_area.addWidget(self.chat_placeholder)

        main_layout.addLayout(left_panel, 2)
        main_layout.addLayout(self.chat_area, 5)

        self.chat_list.itemClicked.connect(self.open_selected_chat)

        self.load_user_info()
        self.load_chat_partners()

    def load_user_info(self):
        try:
            res = requests.get(f"http://127.0.0.1:5000/user_by_id/{self.user_id}")
            if res.status_code == 200:
                user = res.json()
                self.sender_username = user['username']
                self.username_label.setText(f"👤 {self.sender_username}")
        except:
            self.username_label.setText("👤 [Bilinmeyen]")

    def load_chat_partners(self):
        try:
            res = requests.get(f"http://127.0.0.1:5000/chat_partners/{self.user_id}")
            if res.status_code == 200:
                self.chat_list.clear()
                users = res.json()
                for u in users:
                    item = QListWidgetItem(u["username"])
                    self.chat_list.addItem(item)
        except:
            self.chat_list.addItem("⚠️ Yüklenemedi")

    def open_selected_chat(self, item):
        receiver_username = item.text()
        res = requests.get(f"http://127.0.0.1:5000/user_by_username/{receiver_username}")
        if res.status_code == 200:
            receiver = res.json()
            receiver_id = receiver["user_id"]

            # Önceki pencereyi kaldır
            if self.active_chat:
                self.chat_area.removeWidget(self.active_chat)
                self.active_chat.setParent(None)
                self.active_chat.deleteLater()
                self.active_chat = None

            # Yeni pencereyi oluştur
            self.chat_widget = ChatWindow(
                sender_id=self.user_id,
                sender_username=self.sender_username,
                receiver_id=receiver_id,
                receiver_username=receiver_username
            )
            self.chat_area.addWidget(self.chat_widget)
            self.active_chat = self.chat_widget

    def new_chat(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Yeni Sohbet Başlat")
        dialog.setMinimumWidth(300)

        layout = QVBoxLayout(dialog)
        search_input = QLineEdit()
        search_input.setPlaceholderText("Kullanıcı adı ara...")
        result_list = QListWidget()

        layout.addWidget(search_input)
        layout.addWidget(result_list)

        def search():
            keyword = search_input.text().strip()
            if not keyword:
                return
            try:
                response = requests.get("http://127.0.0.1:5000/users")
                if response.status_code == 200:
                    result_list.clear()
                    users = response.json()
                    for user in users:
                        if keyword.lower() in user["username"].lower() and user["user_id"] != self.user_id:
                            item = QListWidgetItem(f'{user["username"]} ({user["email"]})')
                            item.setData(Qt.UserRole, (user["user_id"], user["username"]))
                            result_list.addItem(item)
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))

        def select_user(item):
            receiver_id, receiver_username = item.data(Qt.UserRole)
            dialog.accept()

            # Listeye ekle
            if not any(self.chat_list.item(i).text() == receiver_username for i in range(self.chat_list.count())):
                self.chat_list.addItem(receiver_username)

            if self.active_chat:
                self.chat_area.removeWidget(self.active_chat)
                self.active_chat.setParent(None)
                self.active_chat.deleteLater()
                self.active_chat = None

            self.chat_widget = ChatWindow(
                sender_id=self.user_id,
                sender_username=self.sender_username,
                receiver_id=receiver_id,
                receiver_username=receiver_username
            )
            self.chat_area.addWidget(self.chat_widget)
            self.active_chat = self.chat_widget

        search_input.textChanged.connect(search)
        result_list.itemClicked.connect(select_user)

        dialog.exec_()
