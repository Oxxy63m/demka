# Точка входа. Запуск: python main.py
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


def main():
    ph_path = "resources/picture.png"
    if not os.path.isfile(ph_path):
        os.makedirs("resources", exist_ok=True)
        img = QImage(300, 200, QImage.Format.Format_RGB32)
        img.fill(0xFFC0C0C0)
        img.save(ph_path)

    app = QApplication(sys.argv)
    app.setApplicationName("Система учёта товаров")
    if os.path.isfile(APP_ICON):
        app.setWindowIcon(QIcon(APP_ICON))
    app.setStyleSheet(f"QWidget{{font-size:{FONT_SIZE}pt;}} QPushButton{{min-height:{BTN_H}px;min-width:100px;}}")
    app.setFont(QFont("", FONT_SIZE))

    while True:
        w = Login()
        if w.exec() != Login.DialogCode.Accepted:
            break
        win = Main(w.get_user())
        win.showMaximized()
        app.exec()
    sys.exit(0)


if __name__ == "__main__":
    main()
