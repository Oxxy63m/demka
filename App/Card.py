# Карточка одного товара в каталоге: фото, описание, цена, скидка, кнопки «В заказ» и «Удалить». Разметка — ui/product_item.ui.
import os
from PySide6.QtWidgets import QFrame, QMenu
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QImage, QColor, QAction
from PySide6.QtUiTools import loadUiType

from App.config import UI, PLACEHOLDER_IMAGE, IMAGE_MAX_WIDTH, IMAGE_MAX_HEIGHT, DATA_DIR

Ui_Card, BaseCard = loadUiType(UI["card"])


def _resolve_product_photo_path(photo_filename):
    if not photo_filename:
        return None
    photo_filename = os.path.basename(str(photo_filename).strip())
    folder = os.path.normpath(os.path.abspath(DATA_DIR))
    if not os.path.isdir(folder):
        return None
    full_path = os.path.normpath(os.path.join(folder, photo_filename))
    if os.path.isfile(full_path):
        return full_path
    try:
        for name in os.listdir(folder):
            if name.lower() == photo_filename.lower():
                return os.path.normpath(os.path.join(folder, name))
    except OSError:
        pass
    return None


def _load_product_photo_pixmap(image_path, width=IMAGE_MAX_WIDTH, height=IMAGE_MAX_HEIGHT):
    full_path = _resolve_product_photo_path(image_path) or _resolve_product_photo_path(PLACEHOLDER_IMAGE) or os.path.normpath(os.path.join(DATA_DIR, PLACEHOLDER_IMAGE))
    pixmap = QPixmap(full_path)
    if pixmap.isNull():
        image = QImage(full_path)
        if not image.isNull():
            pixmap = QPixmap.fromImage(image)
    if not pixmap.isNull():
        return pixmap.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    placeholder_pixmap = QPixmap(width, height)
    placeholder_pixmap.fill(QColor(220, 220, 220))
    return placeholder_pixmap


STOCK_ZERO_BG = "#ADD8E6"
STOCK_ZERO_TEXT = "#003366"


class Card(BaseCard, Ui_Card):
    clicked = Signal(int)
    delete_requested = Signal(int)
    add_to_cart = Signal(dict)  # один элемент корзины: product_id, product_name, price, quantity

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
        if hasattr(self, "btn_delete"):
            self.btn_delete.setVisible(self._is_admin)
            if self._is_admin:
                self.btn_delete.clicked.connect(lambda: self.delete_requested.emit(self.product_id))
        if hasattr(self, "btn_order"):
            self.btn_order.setVisible(self._is_client)
            if self._is_client:
                self.btn_order.clicked.connect(self._emit_add_to_cart)

    def _fill_card(self):
        for label_widget in (
            self.lbl_header, self.lbl_desc_title, self.lbl_desc,
            self.lbl_manufacturer, self.lbl_supplier, self.lbl_price,
            self.lbl_unit, self.lbl_stock, self.discount_label,
        ):
            label_widget.setWordWrap(True)
        category_name = (self.product.get("category_name") or "").strip()
        product_name = (self.product.get("product_name") or "").strip()
        header_text = f"{category_name} | {product_name}" if category_name and product_name else (product_name or category_name or "—")
        self.lbl_header.setText(header_text)
        self.lbl_header.setStyleSheet("font-weight: bold; font-size: 14pt;")
        self.lbl_desc_title.setText("Описание товара:")
        description_text = (self.product.get("description") or "").strip()
        self.lbl_desc.setText(description_text or "—")
        self.lbl_manufacturer.setText("Производитель: " + (self.product.get("manufacturer_name") or "—"))
        self.lbl_supplier.setText("Поставщик: " + (self.product.get("supplier_name") or "—"))
        price_value = float(self.product.get("price") or 0)
        discount_percent = float(self.product.get("discount") or 0)
        price_with_discount = price_value * (1 - discount_percent / 100) if discount_percent else price_value
        if discount_percent > 0:
            price_text = f'Цена: <span style="text-decoration:line-through; color:red">{price_value:.2f}</span> <span style="color:black">{price_with_discount:.2f}</span> руб.'
        else:
            price_text = f"Цена: {price_value:.2f} руб."
        self.lbl_price.setText(price_text)
        self.lbl_price.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_unit.setText("Единица измерения: " + (self.product.get("unit_name") or "—"))
        self.lbl_stock.setText("Количество на складе: " + str(int(self.product.get("stock_quantity") or 0)))
        discount_display = int(discount_percent) if discount_percent == int(discount_percent) else discount_percent
        self.discount_label.setText("Действующая скидка\n\n" + (f"{discount_display} %" if discount_percent else "—"))
        self.discount_label.setStyleSheet("font-weight: bold; padding: 8px; background: #f8f8f8;")
        self.photo_label.setPixmap(_load_product_photo_pixmap(self.product.get("photo")))
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

    def _emit_add_to_cart(self):
        price = float(self.product.get("price") or 0)
        discount = float(self.product.get("discount") or 0)
        price_with_discount = price * (1 - discount / 100) if discount else price
        self.add_to_cart.emit({
            "product_id": self.product_id,
            "product_name": (self.product.get("product_name") or "").strip() or "—",
            "price": price_with_discount,
            "quantity": 1,
        })

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
