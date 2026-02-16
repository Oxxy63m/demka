import os
import sys

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import auth_user


class LoginWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Вход в систему")
        self.setMinimumWidth(360)
        self.user = None

        layout = QVBoxLayout(self)
        title = QLabel("Система учёта товаров")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        layout.addWidget(QLabel("Логин:"))
        self.login_edit = QLineEdit()
        layout.addWidget(self.login_edit)

        layout.addWidget(QLabel("Пароль:"))
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_edit)

        btn_layout = QHBoxLayout()
        btn_login = QPushButton("Войти")
        btn_login.clicked.connect(self.on_login)
        btn_guest = QPushButton("Войти как гость")
        btn_guest.clicked.connect(self.on_guest)
        btn_layout.addWidget(btn_login)
        btn_layout.addWidget(btn_guest)
        layout.addLayout(btn_layout)

    def on_login(self):
        login = self.login_edit.text().strip()
        password = self.password_edit.text().strip()
        if not login:
            QMessageBox.warning(self, "Ошибка", "Введите логин.")
            return
        try:
            user = auth_user(login, password)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка БД: {e}")
            return
        if not user:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль.")
            return
        self.user = user
        self.accept()

    def on_guest(self):
        self.user = {"full_name": "Гость", "role": "guest"}
        self.accept()

    def get_user(self):
        return self.user
