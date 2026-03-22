# Card.py
import os

from PySide6.QtWidgets import QFrame
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPixmap
from PySide6.QtUiTools import loadUiType

from App.config import PLACEHOLDER_PHOTO, UI

Ui_ProductCard, BaseProductCard = loadUiType(UI["card"])


class Card(BaseProductCard, Ui_ProductCard):
    clicked = Signal(int)
    delete_requested = Signal(int)

    def __init__(self, product, parent=None, is_admin=False):
        super().__init__(parent)
        self.setupUi(self)
        self.product = product
        self.product_id = product.get("product_id")
        self._is_admin = is_admin
        self._pix = QPixmap()

        self.setObjectName("ProductCard")
        self.photo_label.setObjectName("photo_label")
        self.discount_label.setObjectName("discount_label")

        self.main_layout.setStretch(0, 2)
        self.main_layout.setStretch(1, 5)
        self.main_layout.setStretch(2, 1)
        self.photo_label.setMinimumSize(160, 107)
        self.photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.discount_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        raw = product.get("photo")
        if raw and not isinstance(raw, str):
            self._pix.loadFromData(bytes(memoryview(raw)))
        elif isinstance(raw, str) and raw.strip():
            self._pix = QPixmap(os.path.join("resources", raw.strip()))
        if self._pix.isNull():
            self._pix = QPixmap(PLACEHOLDER_PHOTO)

        cat = (product.get("category_name") or "").strip()
        name = (product.get("product_name") or "").strip()
        self.lbl_header.setText(f"{cat} | {name}" if cat and name else (name or cat or "—"))

        d = (product.get("description") or "").strip()
        self.lbl_description.setText("Описание товара: " + (d or "—"))
        self.lbl_manufacturer.setText("Производитель: " + str(product.get("manufacturer_name") or "—"))
        self.lbl_supplier.setText("Поставщик: " + str(product.get("supplier_name") or "—"))

        price = float(product.get("price") or 0)
        disc = float(product.get("discount") or 0)

        self.lbl_unit.setText("Единица измерения: " + str(product.get("unit_name") or "—"))
        self.lbl_stock.setText("Количество на складе: " + str(int(product.get("stock_quantity") or 0)))

        dv = int(disc) if disc == int(disc) else disc
        self.discount_label.setText("Действующая скидка\n" + (f"{dv} %" if disc else "—"))

        for w in (
            self.lbl_header,
            self.lbl_description,
            self.lbl_manufacturer,
            self.lbl_supplier,
            self.lbl_price,
            self.lbl_unit,
            self.lbl_stock,
        ):
            w.setWordWrap(True)

        self._apply_highlight()
        self._set_price_display(price, disc)
        self._photo()
        self.btn_delete.setVisible(is_admin)
        if is_admin:
            self.btn_delete.clicked.connect(lambda: self.delete_requested.emit(self.product_id))

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._photo()

    def _apply_highlight(self):
        disc = float(self.product.get("discount") or 0)
        stock = int(self.product.get("stock_quantity") or 0)
        self.setFrameShape(QFrame.Shape.Box)
        self.setLineWidth(1)
        self._hl = ""

        if disc > 15:
            self._hl = "green"
            self.setStyleSheet(
                "QFrame#ProductCard { border: 2px solid #1e6b3d; background-color: #2E8B57; } "
                "QFrame#ProductCard QFrame#center_frame, QFrame#ProductCard QFrame#right_discount_frame "
                "{ background-color: transparent; border: 1px solid #000000; } "
                "QFrame#ProductCard QLabel { color: #000000; background: transparent; } "
                "QFrame#ProductCard QLabel#lbl_header { font-weight: bold; } "
                "QFrame#ProductCard QLabel#photo_label { color: #000000; background: #e0e0e0; border: 1px solid #000000; } "
                "QFrame#ProductCard QLabel#discount_label { color: #000000; font-weight: bold; } "
                "QFrame#ProductCard QPushButton { color: #000000; background: #f0f0f0; border: 1px solid #000000; min-height: 34px; } "
            )
        elif stock == 0:
            self._hl = "blue"
            self.setStyleSheet(
                "QFrame#ProductCard { border: 1px solid #003366; background-color: #ADD8E6; } "
                "QFrame#ProductCard QFrame#center_frame, QFrame#ProductCard QFrame#right_discount_frame "
                "{ background-color: transparent; border: 1px solid #000000; } "
                "QFrame#ProductCard QLabel { color: #000000; background: transparent; } "
                "QFrame#ProductCard QLabel#lbl_header { font-weight: bold; } "
                "QFrame#ProductCard QLabel#photo_label { color: #000000; background: #d6ecfa; border: 1px solid #000000; } "
                "QFrame#ProductCard QLabel#discount_label { color: #000000; font-weight: bold; } "
                "QFrame#ProductCard QPushButton { color: #000000; background: #ffffff; border: 1px solid #000000; min-height: 34px; } "
            )
        else:
            self.setStyleSheet(
                "QFrame#ProductCard { border: 1px solid #000000; background-color: #ffffff; } "
                "QFrame#ProductCard QFrame#center_frame, QFrame#ProductCard QFrame#right_discount_frame "
                "{ background-color: #ffffff; border: 1px solid #000000; } "
                "QFrame#ProductCard QLabel { color: #000000; } "
                "QFrame#ProductCard QLabel#lbl_header { font-weight: bold; } "
                "QFrame#ProductCard QLabel#photo_label { color: #000000; background: #f0f0f0; border: 1px solid #000000; } "
                "QFrame#ProductCard QLabel#discount_label { font-weight: bold; } "
                "QFrame#ProductCard QPushButton { color: #000000; min-height: 34px; } "
            )

    def _set_price_display(self, price, disc):
        if disc <= 0:
            self.lbl_price.setTextFormat(Qt.TextFormat.PlainText)
            self.lbl_price.setText(f"Цена: {price:.2f} руб.")
            return
        newp = price * (1 - disc / 100)
        self.lbl_price.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_price.setText(
            f"Цена: <s style='color:#000000'>{price:.2f}</s> "
            f"<span style='color:#000000;font-weight:bold'>{newp:.2f}</span> руб."
        )

    def _photo(self):
        w, h = max(self.photo_label.width(), 1), max(self.photo_label.height(), 1)
        if self._pix.isNull():
            self.photo_label.clear()
            return
        self.photo_label.setPixmap(
            self._pix.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        )

    def sizeHint(self):
        return QSize(480, 180)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self.product_id and self._is_admin:
            self.clicked.emit(self.product_id)
        super().mousePressEvent(e)
