import os
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage, QFont, QIcon

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from App.config import APP_ICON
from App.Login import Login
from App.Main import Main

FONT_SIZE = 16
BTN_H = 42


def _ensure_placeholder_image():
    placeholder_path = "resources/picture.png"
    if os.path.isfile(placeholder_path):
        return
    os.makedirs("resources", exist_ok=True)
    image = QImage(300, 200, QImage.Format.Format_RGB32)
    image.fill(0xFFC0C0C0)
    image.save(placeholder_path)


def _setup_app_style(app):
    app.setApplicationName("Система учёта товаров")
    if os.path.isfile(APP_ICON):
        app.setWindowIcon(QIcon(APP_ICON))
    app.setFont(QFont("Times New Roman", FONT_SIZE))
    app.setStyleSheet(
        f"QWidget{{font-size:{FONT_SIZE}pt;}}"
        f" QPushButton{{min-height:{BTN_H}px;min-width:100px;}}"
    )


def main():
    _ensure_placeholder_image()
    app = QApplication(sys.argv)
    _setup_app_style(app)

    while True:
        login_dialog = Login()
        if login_dialog.exec() != Login.DialogCode.Accepted:
            break
        main_window = Main(login_dialog.get_user())
        main_window.showMaximized()
        app.exec()
    sys.exit(0)


if __name__ == "__main__":
    main()
