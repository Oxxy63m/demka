# Окно входа в систему. Разметка из ui/login.ui.
from PySide6.QtWidgets import QDialog, QMessageBox
from PySide6.QtGui import QPixmap
from PySide6.QtUiTools import loadUiType

from App.config import UI
from logic.auth import login as do_login, get_guest_user

Ui_Login, BaseLogin = loadUiType(UI["login"])


class Login(BaseLogin, Ui_Login):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.user = None
        self.setWindowTitle("Вход в систему")
        # Пароль скрыт точками
        self.password_edit.setEchoMode(self.password_edit.EchoMode.Password)
        self.btn_login.clicked.connect(self._login)
        self.btn_guest.clicked.connect(self._guest)
        self._show_logo()

    def _show_logo(self):
        """Показать картинку логотипа на экране входа."""
        picture = QPixmap("resources/icon.png")
        self.lbl_logo.setPixmap(picture)

    def _login(self):
        """Проверить логин и пароль, если верно — закрыть окно с результатом."""
        login_text = self.login_edit.text().strip()
        password_text = self.password_edit.text().strip()
        try:
            user = do_login(login_text, password_text)
        except Exception as error:
            QMessageBox.critical(self, "Ошибка", str(error))
            return
        if user is None:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль.")
            return
        self.user = user
        self.accept()

    def _guest(self):
        """Войти как гость без логина."""
        self.user = get_guest_user()
        self.accept()

    def get_user(self):
        """Вернуть выбранного пользователя (или None)."""
        return self.user
