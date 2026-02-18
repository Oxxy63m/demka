# App/ProdForm.py — форма товара, разметка из UI/product_form.ui
import os
from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtUiTools import loadUiType

from App.config import UI, ROOT, DATA_DIR, IMAGES_FOLDER, IMAGE_MAX_WIDTH, IMAGE_MAX_HEIGHT, PLACEHOLDER_IMAGE
from logic.product_edit import (
    load_product as load_product_by_id,
    save_product as save_product_to_db,
    get_category_names,
    get_manufacturer_names,
)

Ui_ProdForm, BaseProdForm = loadUiType(UI["prod"])


def _placeholder():
    path = os.path.join(ROOT, "resources", PLACEHOLDER_IMAGE)
    if os.path.isfile(path):
        pix = QPixmap(path)
        if not pix.isNull():
            return pix.scaled(IMAGE_MAX_WIDTH, IMAGE_MAX_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    pix = QPixmap(IMAGE_MAX_WIDTH, IMAGE_MAX_HEIGHT)
    pix.fill(Qt.GlobalColor.lightGray)
    return pix


def _save_image(path):
    img = QImage(path)
    if img.isNull():
        return ""
    img = img.scaled(IMAGE_MAX_WIDTH, IMAGE_MAX_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    folder = os.path.join(ROOT, IMAGES_FOLDER)
    os.makedirs(folder, exist_ok=True)
    name = os.path.basename(path)
    name = os.path.splitext(name)[0] + ".png"
    full = os.path.join(folder, name)
    n = 0
    while os.path.exists(full):
        n += 1
        name = os.path.splitext(os.path.basename(path))[0] + f"_{n}.png"
        full = os.path.join(folder, name)
    if not img.save(full):
        return ""
    return os.path.join(IMAGES_FOLDER, name)


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
        if hasattr(self, "data_group"):
            self.data_group.setStyleSheet(
                "QGroupBox { font-weight: bold; background-color: #E8F5E9; border: 1px solid #2E8B57; border-radius: 4px; margin-top: 8px; padding-top: 8px; } QGroupBox::title { color: #2E8B57; }"
            )
        if hasattr(self, "photo_group"):
            self.photo_group.setStyleSheet(
                "QGroupBox { font-weight: bold; background-color: #E3F2FD; border: 1px solid #ADD8E6; border-radius: 4px; margin-top: 8px; padding-top: 8px; } QGroupBox::title { color: #1976D2; }"
            )
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
            self.photo_label.setPixmap(_placeholder())

    def _load_product(self):
        try:
            product = load_product_by_id(self.product_id)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            self.reject()
            return
        if not product:
            self.reject()
            return
        self.id_edit.setText(str(product["id"]))
        self.article_edit.setText(product.get("article") or "")
        self.name_edit.setText(product.get("product_name") or "")
        cat = product.get("category") or ""
        idx = self.category_combo.findText(cat)
        if idx >= 0:
            self.category_combo.setCurrentIndex(idx)
        else:
            self.category_combo.setCurrentText(cat)
        self.desc_edit.setPlainText(product.get("description") or "")
        manuf = product.get("manufacturer") or ""
        idx = self.manuf_combo.findText(manuf)
        if idx >= 0:
            self.manuf_combo.setCurrentIndex(idx)
        else:
            self.manuf_combo.setCurrentText(manuf)
        self.supp_edit.setText(product.get("supplier") or "")
        self.price_spin.setValue(float(product.get("price") or 0))
        self.unit_edit.setText(product.get("unit") or "")
        self.qty_spin.setValue(int(product.get("stock_quantity") or 0))
        self.discount_spin.setValue(float(product.get("discount") or 0))
        self.old_photo_path = product.get("photo")
        self._show_photo(self.old_photo_path)

    def _load_photo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите изображение", "", "Изображения (*.png *.jpg *.jpeg)")
        if not path:
            return
        if QPixmap(path).isNull():
            QMessageBox.warning(self, "Ошибка", "Не удалось открыть файл.")
            return
        self.new_photo_path = path
        self._show_photo()

    def _save(self):
        product_name = self.name_edit.text().strip()
        if not product_name:
            QMessageBox.warning(self, "Ошибка", "Введите наименование.")
            return
        photo = self.old_photo_path
        if self.new_photo_path:
            photo = _save_image(self.new_photo_path)
            if not photo:
                QMessageBox.warning(self, "Ошибка", "Не удалось сохранить изображение.")
                return
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
            QMessageBox.information(self, "Готово", "Товар обновлён." if self.is_edit else "Товар добавлен.")
            self.accepted.emit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def _show_photo(self, path=None):
        candidates = [self.new_photo_path]
        if path:
            candidates.append(os.path.join(DATA_DIR, path))
            candidates.append(os.path.join(ROOT, path))
        for fp in candidates:
            if fp and os.path.isfile(fp):
                pix = QPixmap(fp)
                if not pix.isNull():
                    self.photo_label.setPixmap(pix.scaled(IMAGE_MAX_WIDTH, IMAGE_MAX_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                    return
        self.photo_label.setPixmap(_placeholder())
