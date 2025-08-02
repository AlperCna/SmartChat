from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel
import requests
from .signup_window import SignupWindow
from .chat_panel_window import ChatPanelWindow

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SmartChat - Login")
        self.setMinimumWidth(300)
        self.setStyleSheet("""
            QWidget {
                background-color: #121212;
                color: white;
                font-family: 'Segoe UI';
            }
            QLineEdit {
                background-color: #1e1e1e;
                border: 1px solid #444;
                border-radius: 8px;
                padding: 8px;
                color: white;
            }
            QPushButton {
                background-color: #3a87f2;
                color: white;
                border-radius: 8px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #5c9dff;
            }
            QLabel {
                padding: 4px;
            }
        """)

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
                    self.error_label.setStyleSheet("color: lightgreen;")
                    self.error_label.setText("\u2705 Login successful")
                    user_id = data.get("user_id")
                    self.panel_window = ChatPanelWindow(user_id)
                    self.panel_window.show()
                    self.close()
                else:
                    self.error_label.setStyleSheet("color: red;")
                    self.error_label.setText("\u274C " + data.get("error", "Login failed"))
            else:
                try:
                    err_data = r.json()
                    self.error_label.setText("\u274C " + err_data.get("error", "Server error"))
                except:
                    self.error_label.setText("\u274C Server error")
        except Exception as e:
            self.error_label.setText("Error: " + str(e))

    def open_signup(self):
        self.signup_window = SignupWindow()
        self.signup_window.show()
        self.close()