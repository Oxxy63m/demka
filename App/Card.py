import os
from PySide6.QtWidgets import QFrame, QMenu
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QAction
from PySide6.QtUiTools import loadUiType

from App.config import UI

Ui_Card, BaseCard = loadUiType(UI["card"])


def _photo_pixmap(photo_filename, width=300, height=200):
    path = os.path.join("resources", photo_filename or "picture.png")
    pixmap = QPixmap(path)
    if pixmap.isNull():
        pixmap = QPixmap("resources/picture.png")
    return pixmap.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)


def _calc_price_with_discount(price, discount_percent):
    if discount_percent:
        return price * (1 - discount_percent / 100)
    return price


def _format_discount_value(discount_percent):
    if not discount_percent:
        return "—"
    if discount_percent == int(discount_percent):
        return int(discount_percent)
    return discount_percent


STOCK_ZERO_BG = "#ADD8E6"
STOCK_ZERO_TEXT = "#003366"


class Card(BaseCard, Ui_Card):
    clicked = Signal(int)
    delete_requested = Signal(int)

    def __init__(self, product, parent=None, is_admin=False, is_client=False):
        super().__init__(parent)
        self.setupUi(self)
        self.product = product
        self.product_id = product.get("product_id")
        self._is_admin = is_admin
        self._is_client = is_client
        self.setMinimumHeight(200)
        self._fill_card()
        self._apply_highlight()
        self.btn_delete.setVisible(self._is_admin)
        if self._is_admin:
            self.btn_delete.clicked.connect(self._on_delete_clicked)


    def _on_delete_clicked(self):
        self.delete_requested.emit(self.product_id)

    def _on_context_edit(self, checked=False):
        self.clicked.emit(self.product_id)

    def _on_context_delete(self, checked=False):
        self.delete_requested.emit(self.product_id)

    def _fill_card(self):
        self.lbl_header.setWordWrap(True)
        self.lbl_desc_title.setWordWrap(True)
        self.lbl_desc.setWordWrap(True)
        self.lbl_manufacturer.setWordWrap(True)
        self.lbl_supplier.setWordWrap(True)
        self.lbl_price.setWordWrap(True)
        self.lbl_unit.setWordWrap(True)
        self.lbl_stock.setWordWrap(True)
        self.discount_label.setWordWrap(True)

        category_name = (self.product.get("category_name") or "").strip()
        product_name = (self.product.get("product_name") or "").strip()
        if category_name and product_name:
            header_text = category_name + " | " + product_name
        elif product_name:
            header_text = product_name
        elif category_name:
            header_text = category_name
        else:
            header_text = "—"

        self.lbl_header.setText(header_text)
        self.lbl_header.setStyleSheet("font-weight: bold; font-size: 14pt;")

        self.lbl_desc_title.setText("Описание товара:")

        description_text = (self.product.get("description") or "").strip()
        if description_text:
            self.lbl_desc.setText(description_text)
        else:
            self.lbl_desc.setText("—")

        manufacturer_name = self.product.get("manufacturer_name") or "—"
        supplier_name = self.product.get("supplier_name") or "—"
        unit_name = self.product.get("unit_name") or "—"
        stock_quantity = int(self.product.get("stock_quantity") or 0)
        price_value = float(self.product.get("price") or 0)
        discount_percent = float(self.product.get("discount") or 0)

        self.lbl_manufacturer.setText("Производитель: " + manufacturer_name)
        self.lbl_supplier.setText("Поставщик: " + supplier_name)
        self.lbl_unit.setText("Единица измерения: " + unit_name)
        self.lbl_stock.setText("Количество на складе: " + str(stock_quantity))

        price_with_discount = _calc_price_with_discount(price_value, discount_percent)

        if discount_percent > 0:
            price_text = (
                "Цена: "
                f'<span style="text-decoration:line-through; color:red">{price_value:.2f}</span> '
                f"<span style=\"color:black\">{price_with_discount:.2f}</span> руб."
            )
        else:
            price_text = f"Цена: {price_value:.2f} руб."

        self.lbl_price.setText(price_text)
        self.lbl_price.setTextFormat(Qt.TextFormat.RichText)

        discount_value = _format_discount_value(discount_percent)
        if discount_value == "—":
            discount_text = "—"
        else:
            discount_text = f"{discount_value} %"

        self.discount_label.setText("Действующая скидка\n\n" + discount_text)
        self.discount_label.setStyleSheet("font-weight: bold; padding: 8px; background: #f8f8f8;")
        self.photo_label.setPixmap(_photo_pixmap(self.product.get("photo")))
        self.photo_label.setStyleSheet("background: #f0f0f0;")

    def _apply_highlight(self):
        discount_percent = float(self.product.get("discount") or 0)
        stock_quantity = int(self.product.get("stock_quantity") or 0)
        self.setFrameShape(QFrame.Shape.Box)
        self.setLineWidth(1)
        if discount_percent > 15:
            self.setStyleSheet(
                f"QFrame#ProductCard {{ border: 1px solid #1e6b3d; background-color: #2E8B57; }}"
            )
        elif stock_quantity == 0:
            self.setStyleSheet(
                f"QFrame#ProductCard {{ border: 1px solid #003366; background-color: {STOCK_ZERO_BG}; color: {STOCK_ZERO_TEXT}; }} "
                f"QFrame#ProductCard QLabel {{ color: {STOCK_ZERO_TEXT}; }}"
            )
        else:
            self.setStyleSheet("QFrame#ProductCard { border: 1px solid #ccc; background-color: #fff; }")

    def get_product_id(self):
        return self.product_id

    def contextMenuEvent(self, event):
        if not self._is_admin or not self.product_id:
            return
        menu = QMenu(self)
        act_edit = QAction("Редактировать", self)
        act_edit.triggered.connect(self._on_context_edit)
        menu.addAction(act_edit)
        act_del = QAction("Удалить", self)
        act_del.triggered.connect(self._on_context_delete)
        menu.addAction(act_del)
        menu.exec(event.globalPos())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.product_id:
            self.clicked.emit(self.product_id)
        super().mousePressEvent(event)
