# frontend/main.py
from PyQt5.QtWidgets import QApplication
from frontend.ui.chat_window import ChatWindow
import sys

app = QApplication(sys.argv)

# Pencere 1: Kullanıcı 1 (1 → 2)
window1 = ChatWindow(sender_id=1, receiver_id=2)
window1.show()

# Pencere 2: Kullanıcı 2 (2 → 1)
window2 = ChatWindow(sender_id=2, receiver_id=1)
window2.show()

sys.exit(app.exec_())
