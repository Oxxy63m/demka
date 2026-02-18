# Точка входа приложения (структура как DemoExamenShoes: App + UI)
import os
import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage, QFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from App.config import IMAGE_MAX_WIDTH, IMAGE_MAX_HEIGHT, PLACEHOLDER_IMAGE, ROOT
from App.Login import Login
from App.Main import Main

# Крупный интерфейс: шрифт ~2x, кнопки в 1.5 раза больше
APP_FONT_SIZE = 16
APP_FONT_SIZE_SMALL = 13
BUTTON_MIN_HEIGHT = 42


def app_stylesheet():
    return f"""
    QWidget {{ font-size: {APP_FONT_SIZE}pt; }}
    QLabel {{ font-size: {APP_FONT_SIZE}pt; }}
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QDateEdit {{ font-size: {APP_FONT_SIZE}pt; min-height: 28px; }}
    QPushButton {{ font-size: {APP_FONT_SIZE}pt; min-height: {BUTTON_MIN_HEIGHT}px; min-width: 100px; }}
    QTableWidget {{ font-size: {APP_FONT_SIZE_SMALL}pt; }}
    QGroupBox {{ font-size: {APP_FONT_SIZE}pt; font-weight: bold; }}
    QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; }}
    """


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
    app.setStyleSheet(app_stylesheet())
    font = QFont()
    font.setPointSize(APP_FONT_SIZE)
    app.setFont(font)
    while True:
        login = Login()
        if login.exec() != Login.DialogCode.Accepted:
            break
        win = Main(login.get_user())
        win.showMaximized()
        app.exec()
    sys.exit(0)


if __name__ == "__main__":
    main()
