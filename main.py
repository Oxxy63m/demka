import os
import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import IMAGE_MAX_WIDTH, IMAGE_MAX_HEIGHT, PLACEHOLDER_IMAGE
from ui.login_window import LoginWindow
from ui.product_list_window import ProductListWindow

ROOT = os.path.dirname(os.path.abspath(__file__))


def main():
    resources_dir = os.path.join(ROOT, "resources")
    placeholder_path = os.path.join(resources_dir, PLACEHOLDER_IMAGE)
    if not os.path.isfile(placeholder_path):
        os.makedirs(resources_dir, exist_ok=True)
        img = QImage(IMAGE_MAX_WIDTH, IMAGE_MAX_HEIGHT, QImage.Format.Format_RGB32)
        img.fill(0xFFC0C0C0)
        img.save(placeholder_path)
    app = QApplication(sys.argv)
    app.setApplicationName("Система учёта товаров")
    while True:
        login = LoginWindow()
        if login.exec() != LoginWindow.DialogCode.Accepted:
            break
        win = ProductListWindow(login.get_user())
        win.showMaximized()
        app.exec()
    sys.exit(0)


if __name__ == "__main__":
    main()
