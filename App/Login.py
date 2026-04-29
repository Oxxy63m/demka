# Login.py
from PySide6.QtGui import QPixmap
from PySide6.QtUiTools import loadUiType

from App.config import ui_path
from App.db import auth_user

Ui_Login, BaseLogin = loadUiType(ui_path("login"))


class Login(BaseLogin, Ui_Login):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.user = None
        self.setWindowTitle("Вход")
        self.btn_login.clicked.connect(self.login_clicked)
        self.btn_guest.clicked.connect(self.guest_clicked)
        self.lbl_logo.setPixmap(QPixmap("resources/icon.png"))

    def login_clicked(self):
        self.user = auth_user(self.login_edit.text(), self.password_edit.text())
        if self.user:
            self.accept()

    def guest_clicked(self):
        self.user = {"full_name": "Гость", "role_name": "guest", "user_role": "guest", "user_id": None}
        self.accept()

    def get_user(self):
        return self.user
