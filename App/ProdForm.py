# Форма добавления и редактирования товара: поля артикула, названия, категории, цены, фото и т.д. Разметка — ui/product_form.ui.
import os
from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtUiTools import loadUiType

from App.config import UI, DATA_DIR, IMAGE_MAX_WIDTH, IMAGE_MAX_HEIGHT, PLACEHOLDER_IMAGE
from App.Card import _resolve_product_photo_path
from logic.product_edit import (
    load_product as load_product_by_id,
    save_product as save_product_to_db,
    get_category_names,
    get_manufacturer_names,
)

Ui_ProdForm, BaseProdForm = loadUiType(UI["prod"])


def _placeholder_pixmap():
    path = _resolve_product_photo_path(PLACEHOLDER_IMAGE) or os.path.join(DATA_DIR, PLACEHOLDER_IMAGE)
    if os.path.isfile(path):
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            return pixmap.scaled(IMAGE_MAX_WIDTH, IMAGE_MAX_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    gray_pixmap = QPixmap(IMAGE_MAX_WIDTH, IMAGE_MAX_HEIGHT)
    gray_pixmap.fill(Qt.GlobalColor.lightGray)
    return gray_pixmap


def _save_uploaded_image_to_folder(source_file_path):
    image = QImage(source_file_path)
    if image.isNull():
        return ""
    image = image.scaled(IMAGE_MAX_WIDTH, IMAGE_MAX_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    os.makedirs(DATA_DIR, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(source_file_path))[0] + ".png"
    full_path = os.path.join(DATA_DIR, base_name)
    counter = 0
    while os.path.exists(full_path):
        counter += 1
        base_name = os.path.splitext(os.path.basename(source_file_path))[0] + f"_{counter}.png"
        full_path = os.path.join(DATA_DIR, base_name)
    if not image.save(full_path):
        return ""
    return base_name


class ProdForm(BaseProdForm, Ui_ProdForm):
    accepted = Signal()

    def __init__(self, product_id, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.product_id = product_id
        self.is_edit = product_id is not None
        self.new_photo_path = None
        self.old_photo_path = None
        self.setWindowTitle("Редактирование товара" if self.is_edit else "Добавление товара")
        self.article_edit.setPlaceholderText("Артикул товара")
        self.name_edit.setPlaceholderText("Обязательное поле")
        self.unit_edit.setPlaceholderText("шт.")
        self.desc_edit.setMaximumHeight(70)
        self.photo_label.setStyleSheet("border:1px solid #ccc;background:#f0f0f0")
        self.category_combo.addItem("")
        for c in get_category_names():
            self.category_combo.addItem(c)
        self.manuf_combo.addItem("")
        for m in get_manufacturer_names():
            self.manuf_combo.addItem(m)
        if not self.is_edit:
            self.id_edit.setVisible(False)
            self.lbl_id.setVisible(False)
        self.btn_photo.clicked.connect(self._load_photo)
        self.btn_save.clicked.connect(self._save)
        self.btn_cancel.clicked.connect(self.reject)
        if self.is_edit:
            self._load_product()
        else:
            self.photo_label.setPixmap(_placeholder_pixmap())

    def _load_product(self):
        try:
            product = load_product_by_id(self.product_id)
        except Exception as error:
            QMessageBox.critical(self, "Ошибка", str(error))
            self.reject()
            return
        if not product:
            self.reject()
            return
        self.id_edit.setText(str(product.get("product_id", "")))
        self.article_edit.setText(product.get("article") or "")
        self.name_edit.setText(product.get("product_name") or "")
        category_value = product.get("category_name") or ""
        category_index = self.category_combo.findText(category_value)
        if category_index >= 0:
            self.category_combo.setCurrentIndex(category_index)
        else:
            self.category_combo.setCurrentText(category_value)
        self.desc_edit.setPlainText(product.get("description") or "")
        manufacturer_value = product.get("manufacturer_name") or ""
        manufacturer_index = self.manuf_combo.findText(manufacturer_value)
        if manufacturer_index >= 0:
            self.manuf_combo.setCurrentIndex(manufacturer_index)
        else:
            self.manuf_combo.setCurrentText(manufacturer_value)
        self.supp_edit.setText(product.get("supplier_name") or "")
        self.price_spin.setValue(float(product.get("price") or 0))
        self.unit_edit.setText(product.get("unit_name") or "")
        self.qty_spin.setValue(int(product.get("stock_quantity") or 0))
        self.discount_spin.setValue(float(product.get("discount") or 0))
        self.old_photo_path = product.get("photo")
        self._show_photo(self.old_photo_path)

    def _load_photo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите изображение", "", "Изображения (*.png *.jpg *.jpeg)")
        if path and not QPixmap(path).isNull():
            self.new_photo_path = path
            self._show_photo()

    def _save(self):
        product_name = self.name_edit.text().strip()
        if not product_name:
            QMessageBox.warning(self, "Ошибка", "Введите наименование.")
            return
        photo = self.old_photo_path
        if self.new_photo_path:
            photo = _save_uploaded_image_to_folder(self.new_photo_path) or photo
        data = {
            "article": self.article_edit.text().strip(),
            "product_name": product_name,
            "category": self.category_combo.currentText().strip(),
            "description": self.desc_edit.toPlainText().strip(),
            "manufacturer": self.manuf_combo.currentText().strip(),
            "supplier": self.supp_edit.text().strip(),
            "price": self.price_spin.value(),
            "unit": self.unit_edit.text().strip() or "шт.",
            "stock_quantity": self.qty_spin.value(),
            "discount": self.discount_spin.value(),
            "photo": photo,
        }
        try:
            save_product_to_db(
                self.product_id if self.is_edit else None,
                data,
                old_photo_path=self.old_photo_path if self.is_edit else None,
            )
            self.accepted.emit()
            self.accept()
        except Exception as error:
            QMessageBox.critical(self, "Ошибка", str(error))

    def _show_photo(self, path=None):
        path_candidates = [self.new_photo_path]
        if path:
            path_candidates.append(_resolve_product_photo_path(path))
            path_candidates.append(os.path.join(DATA_DIR, path))
        for file_path in path_candidates:
            if file_path and os.path.isfile(file_path):
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():
                    self.photo_label.setPixmap(pixmap.scaled(IMAGE_MAX_WIDTH, IMAGE_MAX_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                    return
        self.photo_label.setPixmap(_placeholder_pixmap())
