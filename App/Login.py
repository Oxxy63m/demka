# App/Login.py — диалог входа, разметка из UI/login.ui
import os
import sys
from PySide6.QtWidgets import QDialog, QMessageBox
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtCore import Qt
from PySide6.QtUiTools import loadUiType

from App.config import UI, LOGIN_LOGO
from logic.auth import login as auth_login, get_guest_user

Ui_Login, BaseLogin = loadUiType(UI["login"])


class Login(BaseLogin, Ui_Login):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.user = None
        self.setWindowTitle("Вход в систему")
        self.lbl_title.setFont(QFont("", 18, QFont.Weight.Bold))
        self.password_edit.setEchoMode(self.password_edit.EchoMode.Password)
        self.btn_login.clicked.connect(self._on_login)
        self.btn_guest.clicked.connect(self._on_guest)
        self._set_logo()

    def _set_logo(self):
        if not os.path.isfile(LOGIN_LOGO):
            return
        pixmap = QPixmap(LOGIN_LOGO)
        if pixmap.isNull():
            return
        size = 120
        scaled = pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.lbl_logo.setPixmap(scaled)
        self.lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def _on_login(self):
        login = self.login_edit.text().strip()
        password = self.password_edit.text().strip()
        if not login:
            QMessageBox.warning(self, "Ошибка ввода", "Введите логин.", QMessageBox.StandardButton.Ok)
            return
        try:
            user = auth_login(login, password)
        except Exception as database_error:
            QMessageBox.critical(self, "Ошибка", f"Ошибка БД: {database_error}", QMessageBox.StandardButton.Ok)
            return
        if not user:
            QMessageBox.warning(self, "Ошибка входа", "Неверный логин или пароль.", QMessageBox.StandardButton.Ok)
            return
        self.user = user
        self.accept()

    def _on_guest(self):
        self.user = get_guest_user()
        self.accept()

    def get_user(self):
        return self.user
