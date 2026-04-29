# Card.py
import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtUiTools import loadUiType
from PySide6.QtWidgets import QWidget

from App.config import PLACEHOLDER_PHOTO, RESOURCES_DIR, ui_path

Ui_ProductCard, BaseProductCard = loadUiType(ui_path("card"))


class Card(BaseProductCard, Ui_ProductCard):
    clicked = Signal(int)
    delete_requested = Signal(int)

    def __init__(self, product, parent=None, is_admin=False):
        super().__init__(parent)
        self.setupUi(self)

        self.product = product
        self.is_admin = is_admin

        pid = product.get("product_id")
        self.product_id = int(pid) if pid is not None else None

        # Заголовок
        category = (product.get("category_name") or "").strip()
        name = (product.get("product_name") or "").strip()
        if category and name:
            self.lbl_header.setText(category + " | " + name)
        else:
            self.lbl_header.setText(name or category or "—")

        # Описание/поля
        description = (product.get("description") or "").strip()
        self.lbl_description.setText("Описание товара: " + (description or "—"))
        self.lbl_manufacturer.setText("Производитель: " + str(product.get("manufacturer_name") or "—"))
        self.lbl_supplier.setText("Поставщик: " + str(product.get("supplier_name") or "—"))
        self.lbl_unit.setText("Единица измерения: " + str(product.get("unit_name") or "—"))
        self.lbl_stock.setText("Количество на складе: " + str(int(product.get("stock_quantity") or 0)))

        # Скидка
        price = float(product.get("price") or 0)
        discount = float(product.get("discount") or 0)
        dv = int(discount) if discount == int(discount) else discount
        self.discount_label.setText("Действующая скидка\n" + (f"{dv} %" if discount else "—"))

        # Цена
        if discount <= 0:
            self.lbl_price.setTextFormat(Qt.TextFormat.PlainText)
            self.lbl_price.setText(f"Цена: {price:.2f} руб.")
        else:
            new_price = price * (1 - discount / 100)
            self.lbl_price.setTextFormat(Qt.TextFormat.RichText)
            self.lbl_price.setText(
                f"Цена: <s style='color:red'>{price:.2f}</s> "
                f"<span style='color:#000000;font-weight:bold'>{new_price:.2f}</span> руб."
            )

        # Фото
        photo = (product.get("photo") or "").strip()
        full_path = os.path.join(RESOURCES_DIR, photo) if photo else ""
        pix = QPixmap(full_path) if full_path and os.path.isfile(full_path) else QPixmap()
        if pix.isNull():
            pix = QPixmap(PLACEHOLDER_PHOTO)
        self.photo_label.setPixmap(
            pix.scaled(300, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        )

        # Подсветка по заданию
        stock = int(product.get("stock_quantity") or 0)
        if discount > 15:
            self.setStyleSheet("QFrame#ProductCard { background-color: #2E8B57; }")
        elif stock == 0:
            self.setStyleSheet("QFrame#ProductCard { background-color: #ADD8E6; }")
        else:
            self.setStyleSheet("QFrame#ProductCard { background-color: #ffffff; }")

        # Кнопка удаления (только для админа)
        self.btn_delete.setVisible(is_admin)
        if is_admin:
            self.btn_delete.clicked.connect(lambda: self.delete_requested.emit(self.product_id))
            for w in self.findChildren(QWidget):
                if w is not self.btn_delete:
                    w.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self.is_admin and self.product_id:
            self.clicked.emit(self.product_id)
        super().mousePressEvent(e)
