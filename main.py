# main.py
import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QIcon

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from App.config import APP_ICON
from App.Login import Login
from App.Main import Main

FONT_SIZE = 16
BTN_H = 42


def app_style(app):
    app.setApplicationName("Система учёта товаров")
    app.setWindowIcon(QIcon(APP_ICON))
    app.setFont(QFont("Times New Roman", FONT_SIZE))
    c = "#000000"
    app.setStyleSheet(
        f"QWidget{{font-size:{FONT_SIZE}pt;color:{c};}}"
        f"QLabel{{color:{c};}}"
        f"QLineEdit{{color:{c};}}"
        f"QPlainTextEdit{{color:{c};}}"
        f"QTextEdit{{color:{c};}}"
        f"QComboBox{{color:{c};}}"
        f"QComboBox QAbstractItemView{{color:{c};}}"
        f"QDateEdit{{color:{c};}}"
        f"QSpinBox,QDoubleSpinBox{{color:{c};}}"
        f"QTableWidget{{color:{c};gridline-color:#666;}}"
        f"QHeaderView::section{{color:{c};}}"
        f"QPushButton{{color:{c};min-height:{BTN_H}px;min-width:100px;}}"
        f"QDialogButtonBox{{color:{c};}}"
    )


def main():
    app = QApplication(sys.argv)
    app_style(app)

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
