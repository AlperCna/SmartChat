from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QSizePolicy
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
import requests
from datetime import datetime
import os
import concurrent.futures


class ChatWindow(QWidget):
    def __init__(self, sender_id, sender_username, receiver_id, receiver_username, on_close_callback=None):
        super().__init__()
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.sender_username = sender_username
        self.receiver_username = receiver_username
        self.on_close_callback = on_close_callback

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
        self.media_players = []  # 🎧 Ses çalarları RAM'de tut
        self.setLayout(self.layout)

        # Başlık
        title_layout = QHBoxLayout()
        self.title_label = QLabel(f"💬 Konuşma: {self.receiver_username}")
        self.title_label.setAlignment(Qt.AlignLeft)

        self.close_button = QPushButton("❌")
        self.close_button.setFixedSize(30, 30)
        self.close_button.clicked.connect(self.close_chat_clicked)
        self.close_button.setStyleSheet("background-color: transparent; font-size: 14px;")

        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.close_button)
        self.layout.addLayout(title_layout)

        # Mesaj paneli
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.message_container = QWidget()
        self.message_layout = QVBoxLayout()
        self.message_layout.setAlignment(Qt.AlignTop)
        self.message_container.setLayout(self.message_layout)
        self.scroll.setWidget(self.message_container)
        self.layout.addWidget(self.scroll)

        # Mesaj giriş alanı
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Mesaj yazın...")
        self.send_button = QPushButton("Gönder")

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)
        self.layout.addLayout(input_layout)

        # Öneri kutusu
        self.suggestion_label = QLabel("")
        self.suggestion_label.setStyleSheet("color: #aaa; font-style: italic; padding-left: 4px;")
        self.suggestion_label.setCursor(Qt.PointingHandCursor)
        self.layout.addWidget(self.suggestion_label)
        self.suggestion_label.mousePressEvent = self.accept_suggestion

        # AI tamamlama kutusu
        self.completion_label = QLabel("")
        self.completion_label.setStyleSheet("color: #6cf; font-style: italic; padding-left: 4px;")
        self.completion_label.setCursor(Qt.PointingHandCursor)
        self.layout.addWidget(self.completion_label)
        self.completion_label.mousePressEvent = self.accept_completion

        # Öneri zamanlayıcı (spell suggestion için gecikmeli tetikleme)
        self.suggestion_timer = QTimer()
        self.suggestion_timer.setSingleShot(True)
        self.suggestion_timer.timeout.connect(self._trigger_suggestion)

        # AI tamamlama zamanlayıcı (yazmayı bırakınca tetikleme)
        self.typing_timer = QTimer()
        self.typing_timer.setSingleShot(True)
        self.typing_timer.timeout.connect(self.get_completion)

        # Input değişim bağlantısı
        self.message_input.textChanged.connect(self._schedule_suggestion)
        self.message_input.textChanged.connect(self.handle_typing)

        # Thread havuzu
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

        # Gönder butonu ve enter tuşu
        self.send_button.clicked.connect(self.send_message)
        self.message_input.returnPressed.connect(self.send_message)

        # Mesajları yükle ve yenile
        self.load_messages()
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_messages)
        self.timer.start(3000)

    def close_chat_clicked(self):
        if self.on_close_callback:
            self.on_close_callback()

    def add_message_label(self, text, sender, timestamp):
        time_text = "--:--"
        try:
            dt = datetime.strptime(timestamp, "%a, %d %b %Y %H:%M:%S %Z")
            time_text = dt.strftime("%H:%M")
        except:
            pass

        header = QLabel(f"{sender}  ⏱ {time_text}")
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
        wrapper.setLayout(wrapper_layout)
        wrapper_layout.addWidget(header)
        wrapper_layout.addWidget(body)

        align_wrapper = QWidget()
        align_layout = QHBoxLayout()
        align_wrapper.setLayout(align_layout)

        if sender == self.sender_username:
            align_layout.addStretch()
            align_layout.addWidget(wrapper)
        else:
            align_layout.addWidget(wrapper)
            align_layout.addStretch()

        self.message_layout.addWidget(align_wrapper)

    def add_image_label(self, file_path, sender, timestamp):
        time_text = "--:--"
        try:
            dt = datetime.strptime(timestamp, "%a, %d %b %Y %H:%M:%S %Z")
            time_text = dt.strftime("%H:%M")
        except:
            pass

        header = QLabel(f"{sender}  ⏱ {time_text}")
        header.setStyleSheet("color: #ccc; font-size: 11px; padding-bottom: 2px;")

        image_label = QLabel()
        image_label.setPixmap(QPixmap(file_path).scaledToWidth(250))
        image_label.setStyleSheet("border-radius: 10px; padding: 6px;")

        wrapper = QWidget()
        wrapper_layout = QVBoxLayout()
        wrapper_layout.setContentsMargins(10, 5, 10, 5)
        wrapper.setLayout(wrapper_layout)
        wrapper_layout.addWidget(header)
        wrapper_layout.addWidget(image_label)

        align_wrapper = QWidget()
        align_layout = QHBoxLayout()
        align_wrapper.setLayout(align_layout)

        if sender == self.sender_username:
            align_layout.addStretch()
            align_layout.addWidget(wrapper)
        else:
            align_layout.addWidget(wrapper)
            align_layout.addStretch()

        self.message_layout.addWidget(align_wrapper)

    def add_audio_player(self, file_path, sender, timestamp):
        # Zamanı formatla
        time_text = "--:--"
        try:
            dt = datetime.strptime(timestamp, "%a, %d %b %Y %H:%M:%S %Z")
            time_text = dt.strftime("%H:%M")
        except:
            pass

        # Başlık (isim ve saat)
        header = QLabel(f"{sender}  ⏱ {time_text}")
        header.setStyleSheet("color: #ccc; font-size: 11px; padding-bottom: 2px;")

        # 🎵 ikon
        icon_label = QLabel("🎵")
        icon_label.setFixedWidth(30)
        icon_label.setAlignment(Qt.AlignCenter)

        # ▶️ Oynatma butonu
        play_button = QPushButton("▶️")
        play_button.setFixedSize(30, 30)
        play_button.setStyleSheet("""
            QPushButton {
                background-color: #5c9dff;
                border-radius: 15px;
                color: white;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #3a87f2;
            }
        """)

        # 🎧 MediaPlayer
        media_player = QMediaPlayer(self)
        media_url = QUrl.fromLocalFile(file_path)
        media_player.setMedia(QMediaContent(media_url))

        def play_audio():
            print("▶️ Butona basıldı:", file_path)
            media_player.play()

        play_button.clicked.connect(play_audio)
        self.media_players.append(media_player)

        # 🎚️ Ses barı (ikon + buton)
        audio_bar = QWidget()
        audio_layout = QHBoxLayout()
        audio_layout.setContentsMargins(10, 6, 10, 6)
        audio_bar.setLayout(audio_layout)
        audio_bar.setStyleSheet(f"""
            background-color: {'#3a87f2' if sender == self.sender_username else '#2c2c2c'};
            border-radius: 10px;
        """)

        audio_layout.addWidget(icon_label)
        audio_layout.addWidget(play_button)
        audio_layout.addStretch()

        # Tüm bileşenleri içeren kutu
        wrapper = QWidget()
        wrapper_layout = QVBoxLayout()
        wrapper_layout.setContentsMargins(10, 5, 10, 5)
        wrapper.setLayout(wrapper_layout)
        wrapper_layout.addWidget(header)
        wrapper_layout.addWidget(audio_bar)

        # Sağa/sola hizalama
        align_wrapper = QWidget()
        align_layout = QHBoxLayout()
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
                    if widget:
                        widget.deleteLater()

                for msg in messages:
                    sender_name = self.sender_username if msg["sender_id"] == self.sender_id else self.receiver_username

                    if msg.get("media_type") == "image" and msg.get("file_path"):
                        image_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", msg["file_path"]))
                        self.add_image_label(image_path, sender_name, msg.get("timestamp"))
                    elif msg.get("media_type") == "audio" and msg.get("file_path"):
                        audio_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", msg["file_path"]))
                        self.add_audio_player(audio_path, sender_name, msg.get("timestamp"))
                    else:
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
            self.add_message_label(f"Gönderim hatası: {e}", "Sistem", None)

    def get_suggestion(self):
        text = self.message_input.text().strip()
        if not text:
            self.suggestion_label.setText("")
            return

        def fetch_suggestion():
            try:
                res = requests.post("http://127.0.0.1:5000/suggest", json={
                    "text": text,
                    "user_id": self.sender_id
                })
                if res.status_code == 200:
                    data = res.json()
                    suggested = data.get("punctuated")
                    suggestion_id = data.get("suggestion_id")
                    return (suggested, suggestion_id)
            except:
                return None

        def on_result(result):
            if not result:
                self.suggestion_label.setText("⚠️ Error")
                return
            suggested, suggestion_id = result
            if suggested and suggested != text:
                self.suggestion_label.setText(f"💡 Suggestion: {suggested}")
                self.last_suggestion_id = suggestion_id
            else:
                self.suggestion_label.setText("")

        # ✅ Artık ayrı thread'de çalışıyor
        self.executor.submit(lambda: on_result(fetch_suggestion()))


    def accept_suggestion(self, event):
        text = self.suggestion_label.text().replace("💡 Suggestion: ", "").strip()
        if not text:
            return

        self.message_input.setText(text)
        self.suggestion_label.setText("")

        # Veritabanında accepted=1 yap
        try:
            if hasattr(self, "last_suggestion_id"):
                requests.patch(f"http://127.0.0.1:5000/suggestions/{self.last_suggestion_id}",
                               json={"accepted": True})
        except:
            pass

    def _schedule_suggestion(self):
        self.suggestion_timer.start(600)  # 600 ms sonra öneriyi getir

    def _trigger_suggestion(self):
        self.get_suggestion()

    def get_completion(self):
        text = self.message_input.text().strip()
        if not text:
            self.completion_label.setText("")
            return

        print(">>> get_completion çağrıldı, kullanıcı girdisi:", text)

        try:
            payload = {
                "text": text,
                "receiver_username": self.receiver_username,
                "sender_id": self.sender_id,
                "receiver_id": self.receiver_id
            }
            print(">>> Backend'e gönderilen JSON:", payload)

            res = requests.post("http://127.0.0.1:5000/complete", json=payload)
            print(">>> Backend HTTP status kodu:", res.status_code)

            if res.status_code == 200:
                data = res.json()
                print(">>> Backend cevabı (JSON):", data)
                completion_text = data.get("styled_completion")
                self.last_completion_id = data.get("suggestion_id")
                if completion_text and completion_text != text:
                    self.completion_label.setText(f"✨ AI: {completion_text}")
                else:
                    self.completion_label.setText("")
            else:
                print("!!! Backend hata cevabı (raw):", res.text)
                self.completion_label.setText("⚠️ AI error")

        except Exception as e:
            import traceback
            print("!!! get_completion hata:", str(e))
            traceback.print_exc()
            self.completion_label.setText("⚠️ " + str(e))

    def accept_completion(self, event):
        text = self.completion_label.text().replace("✨ AI: ", "").strip()
        if not text:
            return
        self.message_input.setText(text)
        self.completion_label.setText("")

    # Yeni metot:
    def handle_typing(self):
        text = self.message_input.text()
        if not text:
            return

        last_char = text[-1]
        # 1️⃣ Kelime bitince hemen tetikle
        if last_char in [" ", ".", ",", "?", "!"]:
            self.get_completion()
        else:
            # 2️⃣ Yazmayı bırakırsa 800ms sonra tetikle
            self.typing_timer.start(800)
