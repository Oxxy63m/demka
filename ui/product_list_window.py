import os
import sys

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QLabel, QLineEdit, QComboBox, QPushButton,
    QHeaderView, QMessageBox, QAbstractItemView,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QPixmap

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ROLE_MANAGER, ROLE_ADMINISTRATOR, PLACEHOLDER_IMAGE
from database.db import get_products_all, get_supplier_names, product_in_orders, delete_product

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def photo_pixmap(image_path, size=QSize(80, 60)):
    candidates = [os.path.join(ROOT, image_path) if image_path else "", os.path.join(ROOT, "resources", PLACEHOLDER_IMAGE)]
    for path in candidates:
        if path and os.path.isfile(path):
            pix = QPixmap(path)
            if not pix.isNull():
                return pix.scaled(size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    pix = QPixmap(size)
    pix.fill(QColor(220, 220, 220))
    return pix


class ProductListWindow(QMainWindow):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user = user
        self.role = user.get("role", "guest")
        self.edit_open = False
        self.setWindowTitle("Список товаров")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        head = QHBoxLayout()
        head.addWidget(QLabel("Список товаров"))
        head.addStretch()
        head.addWidget(QLabel(user.get("full_name", "Гость")))
        btn_logout = QPushButton("Выход")
        btn_logout.clicked.connect(self.close)
        head.addWidget(btn_logout)
        layout.addLayout(head)

        if self.role in (ROLE_MANAGER, ROLE_ADMINISTRATOR):
            row = QHBoxLayout()
            row.addWidget(QLabel("Поиск:"))
            self.search_edit = QLineEdit()
            self.search_edit.textChanged.connect(self.refresh_table)
            row.addWidget(self.search_edit)
            row.addWidget(QLabel("Поставщик:"))
            self.supplier_combo = QComboBox()
            self.supplier_combo.addItem("Все поставщики", None)
            self.supplier_combo.currentIndexChanged.connect(self.refresh_table)
            row.addWidget(self.supplier_combo)
            row.addWidget(QLabel("Сортировка:"))
            self.sort_combo = QComboBox()
            self.sort_combo.addItem("—", None)
            self.sort_combo.addItem("По возрастанию кол-ва", "asc")
            self.sort_combo.addItem("По убыванию кол-ва", "desc")
            self.sort_combo.currentIndexChanged.connect(self.refresh_table)
            row.addWidget(self.sort_combo)
            layout.addLayout(row)
            for s in get_supplier_names():
                self.supplier_combo.addItem(s, s)

        if self.role == ROLE_ADMINISTRATOR:
            row = QHBoxLayout()
            btn_add = QPushButton("Добавить товар")
            btn_add.clicked.connect(self.on_add)
            btn_del = QPushButton("Удалить товар")
            btn_del.clicked.connect(self.on_delete)
            row.addWidget(btn_add)
            row.addWidget(btn_del)
            layout.addLayout(row)

        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels(
            ["Фото", "Артикул", "Наименование", "Категория", "Описание", "Производитель", "Поставщик", "Цена", "Ед.", "Кол-во", "Скидка %"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setDefaultSectionSize(70)
        if self.role == ROLE_ADMINISTRATOR:
            self.table.cellDoubleClicked.connect(self.on_edit)
        layout.addWidget(self.table)

        self.refresh_table()

    def refresh_table(self):
        search = self.search_edit.text() if hasattr(self, "search_edit") else ""
        supplier = self.supplier_combo.currentData() if hasattr(self, "supplier_combo") else None
        order_by = self.sort_combo.currentData() if hasattr(self, "sort_combo") else None
        try:
            rows = get_products_all(search, supplier, order_by)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            return
        self.table.setRowCount(len(rows))
        for i, product in enumerate(rows):
            lbl = QLabel()
            lbl.setPixmap(photo_pixmap(product.get("photo")))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setCellWidget(i, 0, lbl)
            self.table.setItem(i, 1, QTableWidgetItem(product.get("article") or ""))
            self.table.setItem(i, 2, QTableWidgetItem(product.get("product_name") or ""))
            self.table.setItem(i, 3, QTableWidgetItem(product.get("category") or ""))
            self.table.setItem(i, 4, QTableWidgetItem((product.get("description") or "")[:80]))
            self.table.setItem(i, 5, QTableWidgetItem(product.get("manufacturer") or ""))
            self.table.setItem(i, 6, QTableWidgetItem(product.get("supplier") or ""))

            price_val = float(product.get("price") or 0)
            discount = float(product.get("discount") or 0)
            qty = int(product.get("stock_quantity") or 0)
            final = price_val * (1 - discount / 100) if discount else price_val

            if discount > 0:
                lbl_price = QLabel()
                lbl_price.setTextFormat(Qt.TextFormat.RichText)
                lbl_price.setText(f'<span style="color:red;text-decoration:line-through">{price_val:.2f}</span> <span style="color:black">{final:.2f}</span>')
                self.table.setCellWidget(i, 7, lbl_price)
            else:
                self.table.setItem(i, 7, QTableWidgetItem(f"{price_val:.2f}"))
            self.table.setItem(i, 8, QTableWidgetItem(product.get("unit") or ""))
            self.table.setItem(i, 9, QTableWidgetItem(str(qty)))
            self.table.setItem(i, 10, QTableWidgetItem(str(discount)))
            self.table.item(i, 2).setData(Qt.ItemDataRole.UserRole, product.get("id"))

            green = QColor("#2E8B57")
            blue = QColor(173, 216, 230)
            for col in range(11):
                it = self.table.item(i, col)
                if it:
                    if discount > 15:
                        it.setBackground(green)
                    elif qty == 0:
                        it.setBackground(blue)
                w = self.table.cellWidget(i, col)
                if w is not None and hasattr(w, "setStyleSheet"):
                    if discount > 15:
                        w.setStyleSheet("background:#2E8B57")
                    elif qty == 0:
                        w.setStyleSheet("background:#ADD8E6")
        self.table.resizeColumnsToContents()

    def current_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        it = self.table.item(row, 2)
        return it.data(Qt.ItemDataRole.UserRole) if it else None

    def open_edit(self, product_id):
        if self.edit_open:
            QMessageBox.warning(self, "Предупреждение", "Закройте окно редактирования.")
            return
        from ui.product_edit_window import ProductEditWindow
        self.edit_open = True
        w = ProductEditWindow(product_id, self)
        w.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        w.destroyed.connect(lambda: setattr(self, "edit_open", False))
        w.accepted.connect(self.refresh_table)
        w.show()

    def on_add(self):
        self.open_edit(None)

    def on_edit(self, row, col):
        item = self.table.item(row, 2)
        product_id = item.data(Qt.ItemDataRole.UserRole) if item else None
        if product_id:
            self.open_edit(product_id)

    def on_delete(self):
        product_id = self.current_id()
        if not product_id:
            QMessageBox.warning(self, "Ошибка", "Выберите товар.")
            return
        if product_in_orders(product_id):
            QMessageBox.warning(self, "Ошибка", "Товар в заказе, удалить нельзя.")
            return
        if QMessageBox.question(self, "Подтверждение", "Удалить товар?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        try:
            delete_product(product_id)
            QMessageBox.information(self, "Готово", "Товар удалён.")
            self.refresh_table()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
