from PyQt5.QtWidgets import QApplication
import sys
from frontend.ui.login_window import LoginWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)


    login = LoginWindow()
    login.setWindowTitle("SmartChat - Login")
    login.show()

    sys.exit(app.exec_())
