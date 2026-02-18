# App/Card.py — карточка товара, разметка из UI/product_item.ui
import os
from PySide6.QtWidgets import QFrame, QMenu
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QColor, QAction
from PySide6.QtUiTools import loadUiType

from App.config import UI, PLACEHOLDER_IMAGE, IMAGE_MAX_WIDTH, IMAGE_MAX_HEIGHT, ROOT, DATA_DIR

Ui_Card, BaseCard = loadUiType(UI["card"])


def _photo_pixmap(image_path, width=IMAGE_MAX_WIDTH, height=IMAGE_MAX_HEIGHT):
    path = ""
    if image_path:
        path = os.path.join(DATA_DIR, image_path)
        if not os.path.isfile(path):
            path = os.path.join(ROOT, image_path)
    if not path or not os.path.isfile(path):
        path = os.path.join(ROOT, "resources", PLACEHOLDER_IMAGE)
    if path and os.path.isfile(path):
        pix = QPixmap(path)
        if not pix.isNull():
            return pix.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    pix = QPixmap(width, height)
    pix.fill(QColor(220, 220, 220))
    return pix


STOCK_ZERO_BG = "#ADD8E6"
STOCK_ZERO_TEXT = "#003366"


class Card(BaseCard, Ui_Card):
    clicked = Signal(int)
    delete_requested = Signal(int)

    def __init__(self, product, parent=None, is_admin=False):
        super().__init__(parent)
        self.setupUi(self)
        self.product = product
        self.product_id = product.get("id")
        self._is_admin = is_admin
        self.setMinimumHeight(200)
        self._fill_card()
        self._apply_highlight()
        if hasattr(self, "btn_delete"):
            self.btn_delete.setVisible(self._is_admin)
            if self._is_admin:
                self.btn_delete.clicked.connect(lambda: self.delete_requested.emit(self.product_id))

    def _fill_card(self):
        cat = (self.product.get("category") or "").strip()
        name = (self.product.get("product_name") or "").strip()
        header = f"{cat} | {name}" if cat and name else (name or cat or "—")
        self.lbl_header.setText(header)
        self.lbl_header.setStyleSheet("font-weight: bold; font-size: 14pt;")
        self.lbl_header.setWordWrap(True)
        self.lbl_desc_title.setText("Описание товара:")
        desc = (self.product.get("description") or "").strip()
        self.lbl_desc.setText(desc or "—")
        self.lbl_manufacturer.setText("Производитель: " + (self.product.get("manufacturer") or "—"))
        self.lbl_supplier.setText("Поставщик: " + (self.product.get("supplier") or "—"))
        price_val = float(self.product.get("price") or 0)
        discount = float(self.product.get("discount") or 0)
        final = price_val * (1 - discount / 100) if discount else price_val
        if discount > 0:
            price_text = f'Цена: <span style="text-decoration:line-through; color:red">{price_val:.2f}</span> <span style="color:black">{final:.2f}</span> руб.'
        else:
            price_text = f"Цена: {price_val:.2f} руб."
        self.lbl_price.setText(price_text)
        self.lbl_price.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_unit.setText("Единица измерения: " + (self.product.get("unit") or "—"))
        self.lbl_stock.setText("Количество на складе: " + str(int(self.product.get("stock_quantity") or 0)))
        discount_val = int(discount) if discount == int(discount) else discount
        self.discount_label.setText("Действующая скидка\n\n" + (f"{discount_val} %" if discount else "—"))
        self.discount_label.setWordWrap(True)
        self.discount_label.setStyleSheet("font-weight: bold; padding: 8px; background: #f8f8f8;")
        self.photo_label.setPixmap(_photo_pixmap(self.product.get("photo")))
        self.photo_label.setStyleSheet("background: #f0f0f0;")

    def _apply_highlight(self):
        discount = float(self.product.get("discount") or 0)
        qty = int(self.product.get("stock_quantity") or 0)
        self.setFrameShape(QFrame.Shape.NoFrame)
        if discount > 15:
            self.setStyleSheet(f"QFrame#ProductCard {{ border: none; background-color: #2E8B57; }}")
        elif qty == 0:
            self.setStyleSheet(
                f"QFrame#ProductCard {{ border: none; background-color: {STOCK_ZERO_BG}; color: {STOCK_ZERO_TEXT}; }} "
                f"QFrame#ProductCard QLabel {{ color: {STOCK_ZERO_TEXT}; }}"
            )
        else:
            self.setStyleSheet("QFrame#ProductCard { border: none; }")

    def get_product_id(self):
        return self.product_id

    def contextMenuEvent(self, event):
        if not self._is_admin or not self.product_id:
            return
        menu = QMenu(self)
        act_edit = QAction("Редактировать", self)
        act_edit.triggered.connect(lambda: self.clicked.emit(self.product_id))
        menu.addAction(act_edit)
        act_del = QAction("Удалить", self)
        act_del.triggered.connect(lambda: self.delete_requested.emit(self.product_id))
        menu.addAction(act_del)
        menu.exec(event.globalPos())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.product_id:
            self.clicked.emit(self.product_id)
        super().mousePressEvent(event)
