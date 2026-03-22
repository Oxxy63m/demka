# ProdForm.py
from PySide6.QtWidgets import QFileDialog
from PySide6.QtCore import Qt, Signal, QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtUiTools import loadUiType

from App.config import PLACEHOLDER_PHOTO, UI
from App.db import get_category_names, get_manufacturer_names, get_product_by_id, insert_product, update_product

Ui_ProdForm, BaseProdForm = loadUiType(UI["prod"])


def _img_bytes(path):
    img = QImage(path)
    if img.isNull():
        return None
    img = img.scaled(300, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    img.save(buf, "PNG")
    return ba.data()


class ProdForm(BaseProdForm, Ui_ProdForm):
    accepted = Signal()

    def __init__(self, product_id, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.product_id = product_id
        self.edit = product_id is not None
        self.photo_bytes = None
        self.setWindowTitle("Товар" if self.edit else "Новый товар")

        self.category_combo.clear()
        self.category_combo.addItem("")
        for x in get_category_names():
            self.category_combo.addItem(x)
        self.manuf_combo.clear()
        self.manuf_combo.addItem("")
        for x in get_manufacturer_names():
            self.manuf_combo.addItem(x)

        if not self.edit:
            self.id_edit.hide()
            self.lbl_id.hide()

        self.btn_photo.clicked.connect(self._pick)
        self.btn_save.clicked.connect(self._save)
        self.btn_cancel.clicked.connect(self.reject)

        if self.edit:
            p = get_product_by_id(self.product_id)
            self.id_edit.setText(str(p["product_id"]))
            self.article_edit.setText(p.get("article") or "")
            self.name_edit.setText(p.get("product_name") or "")
            self.category_combo.setCurrentText(p.get("category_name") or "")
            self.desc_edit.setPlainText(p.get("description") or "")
            self.manuf_combo.setCurrentText(p.get("manufacturer_name") or "")
            self.supp_edit.setText(p.get("supplier_name") or "")
            self.price_spin.setValue(float(p.get("price") or 0))
            self.unit_edit.setText(p.get("unit_name") or "")
            self.qty_spin.setValue(int(p.get("stock_quantity") or 0))
            self.discount_spin.setValue(float(p.get("discount") or 0))
            ph = p.get("photo")
            self.photo_bytes = None if ph is None or isinstance(ph, str) else bytes(memoryview(ph))
            self._prev(self.photo_bytes)
        else:
            self._prev(None)

    def _pick(self):
        path, _ = QFileDialog.getOpenFileName(self, "Фото", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self.photo_bytes = _img_bytes(path)
            self._prev(self.photo_bytes)

    def _prev(self, data):
        pix = QPixmap()
        if data and pix.loadFromData(data):
            self.photo_label.setPixmap(pix.scaled(300, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            pm = QPixmap(PLACEHOLDER_PHOTO)
            self.photo_label.setPixmap(pm.scaled(300, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def _save(self):
        d = {
            "article": self.article_edit.text().strip(),
            "product_name": self.name_edit.text().strip(),
            "category": self.category_combo.currentText().strip(),
            "description": self.desc_edit.toPlainText().strip(),
            "manufacturer": self.manuf_combo.currentText().strip(),
            "supplier": self.supp_edit.text().strip(),
            "price": self.price_spin.value(),
            "unit": self.unit_edit.text().strip() or "шт.",
            "stock_quantity": self.qty_spin.value(),
            "discount": self.discount_spin.value(),
            "photo": self.photo_bytes,
        }
        if self.edit:
            update_product(self.product_id, d)
        else:
            insert_product(d)
        self.accepted.emit()
        self.accept()
