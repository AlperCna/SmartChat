from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel
import requests
from .signup_window import SignupWindow
from .chat_window import ChatWindow

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SmartChat Login")
        self.setMinimumWidth(300)

        layout = QVBoxLayout()

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)

        self.login_button = QPushButton("Login")
        self.signup_button = QPushButton("Sign Up")

        layout.addWidget(self.error_label)
        layout.addWidget(self.email_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)
        layout.addWidget(self.signup_button)

        self.setLayout(layout)

        self.login_button.clicked.connect(self.login)
        self.signup_button.clicked.connect(self.open_signup)

    def login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()

        try:
            r = requests.post("http://127.0.0.1:5000/login", json={
                "email": email,
                "password": password
            })

            if r.status_code == 200:
                data = r.json()
                if data.get("success"):
                    self.error_label.setStyleSheet("color: green;")
                    self.error_label.setText("✅ Login successful")

                    user_id = data.get("user_id")

                    # ✅ Open chat window
                    self.chat_window = ChatWindow(sender_id=user_id, receiver_id=None)  
                    self.chat_window.show()

                    self.close()
                else:
                    self.error_label.setStyleSheet("color: red;")
                    self.error_label.setText("❌ " + data.get("error", "Login failed"))
            else:
                try:
                    err_data = r.json()
                    self.error_label.setText("❌ " + err_data.get("error", "Server error"))
                except:
                    self.error_label.setText("❌ Server error")
        except Exception as e:
            self.error_label.setText("Error: " + str(e))

    def open_signup(self):
        self.signup_window = SignupWindow()
        self.signup_window.show()