# ProdForm.py
import os
import shutil

from PySide6.QtWidgets import QFileDialog
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtUiTools import loadUiType

from App.config import PLACEHOLDER_PHOTO, RESOURCES_DIR, ui_path
from App.db import get_category_names, get_manufacturer_names, get_product_by_id, get_supplier_names, insert_product, update_product

Ui_ProdForm, BaseProdForm = loadUiType(ui_path("prod"))


class ProdForm(BaseProdForm, Ui_ProdForm):
    accepted = Signal()

    def __init__(self, product_id, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.product_id = product_id
        self.edit = product_id is not None
        self._photo_filename = None
        self.setWindowTitle("Товар" if self.edit else "Новый товар")

        self.category_combo.clear()
        self.category_combo.addItem("")
        for x in get_category_names():
            self.category_combo.addItem(x)
        self.manuf_combo.clear()
        self.manuf_combo.addItem("")
        for x in get_manufacturer_names():
            self.manuf_combo.addItem(x)
        # Поставщик — строковое поле; хотя бы покажем известные варианты (tooltip)
        self.supp_edit.setToolTip("\n".join(get_supplier_names()) if hasattr(self, "supp_edit") else "")

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
            self._photo_filename = ph.strip() if isinstance(ph, str) and ph.strip() else None
            pth = os.path.join(RESOURCES_DIR, self._photo_filename) if self._photo_filename else None
            pix = QPixmap(pth) if pth and os.path.isfile(pth) else QPixmap()
            if pix.isNull():
                pix = QPixmap(PLACEHOLDER_PHOTO)
            self.photo_label.setPixmap(
                pix.scaled(300, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            )
        else:
            pix = QPixmap(PLACEHOLDER_PHOTO)
            self.photo_label.setPixmap(
                pix.scaled(300, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            )

    def _pick(self):
        path, _ = QFileDialog.getOpenFileName(self, "Фото", "", "Images (*.png *.jpg *.jpeg)")
        if not path:
            return
        os.makedirs(RESOURCES_DIR, exist_ok=True)
        new_name = os.path.basename(path)
        dest = os.path.join(RESOURCES_DIR, new_name)
        shutil.copy2(path, dest)
        self._photo_filename = new_name
        pix = QPixmap(dest) if os.path.isfile(dest) else QPixmap()
        if pix.isNull():
            pix = QPixmap(PLACEHOLDER_PHOTO)
        self.photo_label.setPixmap(
            pix.scaled(300, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        )

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
            "photo": self._photo_filename,
        }
        if self.edit:
            update_product(self.product_id, d)
        else:
            insert_product(d)
        self.accepted.emit()
        self.accept()
