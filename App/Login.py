# Login.py
from PySide6.QtGui import QPixmap
from PySide6.QtUiTools import loadUiType

from App.config import ui_path
from App.db import auth_user

Ui_Login, BaseLogin = loadUiType(ui_path("login"))

GUEST = {"full_name": "Гость", "role_name": "guest", "role": "guest", "user_id": None}


class Login(BaseLogin, Ui_Login):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.user = None
        self.setWindowTitle("Вход")
        self.btn_login.clicked.connect(self._login)
        self.btn_guest.clicked.connect(self._guest)
        self.lbl_logo.setPixmap(QPixmap("resources/icon.png"))

    def _login(self):
        u = auth_user(self.login_edit.text(), self.password_edit.text())
        if u:
            self.user = u
            self.accept()

    def _guest(self):
        self.user = GUEST
        self.accept()

    def get_user(self):
        return self.user
