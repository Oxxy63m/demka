# Окно входа в систему. Разметка окна берётся из ui/login.ui.
import os
import sys
from PySide6.QtWidgets import QDialog, QMessageBox
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtCore import Qt
from PySide6.QtUiTools import loadUiType
from App.config import UI, LOGIN_LOGO
from logic.auth import login as do_login, get_guest_user

Ui_Login, BaseLogin = loadUiType(UI["login"])


class Login(BaseLogin, Ui_Login):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.user = None
        self.setWindowTitle("Вход в систему")
        self.lbl_title.setFont(QFont("", 18, QFont.Weight.Bold))
        self.password_edit.setEchoMode(self.password_edit.EchoMode.Password)
        self.btn_login.clicked.connect(self._login)
        self.btn_guest.clicked.connect(self._guest)
        self._logo()

    def _logo(self):
        """Показывает логотип на форме входа (файл icon.png из папки данных)."""
        if os.path.isfile(LOGIN_LOGO):
            px = QPixmap(LOGIN_LOGO)
            if not px.isNull():
                self.lbl_logo.setPixmap(px.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def _login(self):
        """Проверяет логин и пароль в БД, при успехе закрывает окно с принятием (accept)."""
        log = self.login_edit.text().strip()
        pwd = self.password_edit.text().strip()
        if not log:
            QMessageBox.warning(self, "Ошибка", "Введите логин.")
            return
        try:
            u = do_login(log, pwd)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            return
        if not u:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль.")
            return
        self.user = u
        self.accept()

    def _guest(self):
        """Вход без пароля: записывает пользователя «Гость» и закрывает окно с принятием."""
        self.user = get_guest_user()
        self.accept()

    def get_user(self):
        """Возвращает данные вошедшего пользователя (словарь с full_name, role и т.д.) или гостя."""
        return self.user
