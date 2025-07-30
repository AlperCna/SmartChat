from PyQt5.QtWidgets import QApplication
import sys
from frontend.ui.login_window import LoginWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Open login windows for both users
    login1 = LoginWindow()
    login1.setWindowTitle("SmartChat - Login (User 1)")
    login1.show()

    login2 = LoginWindow()
    login2.setWindowTitle("SmartChat - Login (User 2)")
    login2.show()

    sys.exit(app.exec_())
