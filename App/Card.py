# Card.py
import os

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtUiTools import loadUiType

from App.config import PLACEHOLDER_PHOTO, RESOURCES_DIR, ui_path

Ui_ProductCard, BaseProductCard = loadUiType(ui_path("card"))

_P = "QFrame#ProductCard"


def _product_card_stylesheet(card_rule: str) -> str:
    """Фон/рамка корневой карточки и жирный заголовок; остальное — как в .ui / системной теме."""
    return (
        f"{_P} {{ {card_rule} }} "
        f"{_P} QLabel#lbl_header {{ font-weight: bold; }} "
    )


class Card(BaseProductCard, Ui_ProductCard):
    clicked = Signal(int)
    delete_requested = Signal(int)

    def __init__(self, product, parent=None, is_admin=False):
        super().__init__(parent)
        self.setupUi(self)
        self.product = product
        pid = product.get("product_id")
        self.product_id = int(pid) if pid is not None else None
        self._is_admin = is_admin

        # Нет имени файла в БД или файла в resources → picture.png
        fn = product.get("photo")
        self._pix = QPixmap()
        if isinstance(fn, str) and fn.strip():
            pth = os.path.join(RESOURCES_DIR, fn.strip())
            if os.path.isfile(pth):
                self._pix = QPixmap(pth)
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

        self._apply_highlight()
        self._set_price_display(price, disc)
        self._photo()
        self.btn_delete.setVisible(is_admin)
        if is_admin:
            self.btn_delete.clicked.connect(
                lambda: self.delete_requested.emit(self.product_id)
            )
            # Дочерние QLabel/QFrame перехватывают мышь; делаем их «прозрачными» для hit-test,
            # чтобы нажатие дошло до этой QFrame (mousePressEvent). Кнопка «Удалить» не трогаем.
            for w in self.findChildren(QWidget):
                if w is not self.btn_delete:
                    w.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            self.setCursor(Qt.CursorShape.PointingHandCursor)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._photo()

    def _apply_highlight(self):
        disc = float(self.product.get("discount") or 0)
        stock = int(self.product.get("stock_quantity") or 0)
        # Метка варианта подсветки; фон карточки — setStyleSheet ниже.
        self._hl = ""

        if disc > 15:
            self._hl = "green"
            self.setStyleSheet(
                _product_card_stylesheet(
                    "background-color: #2E8B57;"
                )
            )
        elif stock == 0:
            self._hl = "blue"
            self.setStyleSheet(
                _product_card_stylesheet(
                    "background-color: #ADD8E6;"
                )
            )
        else:
            self.setStyleSheet(
                _product_card_stylesheet(
                    "background-color: #ffffff;"
                )
            )

    def _set_price_display(self, price, disc):
        if disc <= 0:
            self.lbl_price.setTextFormat(Qt.TextFormat.PlainText)
            self.lbl_price.setText(f"Цена: {price:.2f} руб.")
            return
        newp = price * (1 - disc / 100)
        self.lbl_price.setTextFormat(Qt.TextFormat.RichText)
        # По заданию: старая цена — зачёркнутая, красная; новая (со скидкой) — чёрная.
        self.lbl_price.setText(
            f"Цена: <s style='color:red'>{price:.2f}</s> "
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

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self.product_id and self._is_admin:
            self.clicked.emit(self.product_id)
        super().mousePressEvent(e)
