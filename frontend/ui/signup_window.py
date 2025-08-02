from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel
import requests

class SignupWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SmartChat - Sign Up")
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
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: red;")

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)

        self.signup_button = QPushButton("Create Account")

        layout.addWidget(self.status_label)
        layout.addWidget(self.username_input)
        layout.addWidget(self.email_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.signup_button)

        self.setLayout(layout)
        self.signup_button.clicked.connect(self.signup)

    def signup(self):
        username = self.username_input.text()
        email = self.email_input.text()
        password = self.password_input.text()

        try:
            r = requests.post("http://127.0.0.1:5000/signup", json={
                "username": username,
                "email": email,
                "password": password
            })
            data = r.json()

            if r.status_code == 201:
                self.status_label.setStyleSheet("color: lightgreen;")
                self.status_label.setText("\u2705 Account created. You can log in now.")

                from .login_window import LoginWindow  # ❌ Circular import fix
                self.login_window = LoginWindow()
                self.login_window.show()
                self.close()
            else:
                self.status_label.setStyleSheet("color: red;")
                self.status_label.setText("\u274C " + data.get("error", "Signup failed"))
        except Exception as e:
            self.status_label.setText("Error: " + str(e))