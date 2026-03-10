# Форма добавления и редактирования товара: поля артикула, названия, категории, цены, фото и т.д. Разметка — ui/product_form.ui.
import os
from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtUiTools import loadUiType

from App.config import UI, ROOT, DATA_DIR, IMAGES_FOLDER, IMAGE_MAX_WIDTH, IMAGE_MAX_HEIGHT, PLACEHOLDER_IMAGE
from App.Card import _resolve_product_photo_path
from logic.product_edit import (
    load_product as load_product_by_id,
    save_product as save_product_to_db,
    get_category_names,
    get_manufacturer_names,
)

Ui_ProdForm, BaseProdForm = loadUiType(UI["prod"])


def _placeholder_pixmap():
    """Возвращает изображение-заглушку для поля фото (picture.png или серый прямоугольник)."""
    path = _resolve_product_photo_path(PLACEHOLDER_IMAGE) or os.path.join(DATA_DIR, PLACEHOLDER_IMAGE)
    if os.path.isfile(path):
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            return pixmap.scaled(IMAGE_MAX_WIDTH, IMAGE_MAX_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    gray_pixmap = QPixmap(IMAGE_MAX_WIDTH, IMAGE_MAX_HEIGHT)
    gray_pixmap.fill(Qt.GlobalColor.lightGray)
    return gray_pixmap


def _save_uploaded_image_to_folder(source_file_path):
    """Сохраняет выбранное пользователем изображение в папку проекта и возвращает относительный путь."""
    image = QImage(source_file_path)
    if image.isNull():
        return ""
    image = image.scaled(IMAGE_MAX_WIDTH, IMAGE_MAX_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    images_folder_path = os.path.join(ROOT, IMAGES_FOLDER)
    os.makedirs(images_folder_path, exist_ok=True)
    base_filename = os.path.basename(source_file_path)
    saved_filename = os.path.splitext(base_filename)[0] + ".png"
    full_saved_path = os.path.join(images_folder_path, saved_filename)
    duplicate_counter = 0
    while os.path.exists(full_saved_path):
        duplicate_counter += 1
        saved_filename = os.path.splitext(base_filename)[0] + f"_{duplicate_counter}.png"
        full_saved_path = os.path.join(images_folder_path, saved_filename)
    if not image.save(full_saved_path):
        return ""
    return os.path.join(IMAGES_FOLDER, saved_filename)


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
            self.photo_label.setPixmap(_placeholder_pixmap())

    def _load_product(self):
        """Загружает данные товара из БД и подставляет их в поля формы."""
        try:
            product = load_product_by_id(self.product_id)
        except Exception as load_error:
            QMessageBox.critical(self, "Ошибка", str(load_error))
            self.reject()
            return
        if not product:
            self.reject()
            return
        self.id_edit.setText(str(product["id"]))
        self.article_edit.setText(product.get("article") or "")
        self.name_edit.setText(product.get("product_name") or "")
        category_value = product.get("category") or ""
        category_index = self.category_combo.findText(category_value)
        if category_index >= 0:
            self.category_combo.setCurrentIndex(category_index)
        else:
            self.category_combo.setCurrentText(category_value)
        self.desc_edit.setPlainText(product.get("description") or "")
        manufacturer_value = product.get("manufacturer") or ""
        manufacturer_index = self.manuf_combo.findText(manufacturer_value)
        if manufacturer_index >= 0:
            self.manuf_combo.setCurrentIndex(manufacturer_index)
        else:
            self.manuf_combo.setCurrentText(manufacturer_value)
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
        """Проверяет поля и сохраняет товар в БД (добавление или обновление), затем закрывает форму."""
        product_name = self.name_edit.text().strip()
        if not product_name:
            QMessageBox.warning(self, "Ошибка", "Введите наименование.")
            return
        photo = self.old_photo_path
        if self.new_photo_path:
            photo = _save_uploaded_image_to_folder(self.new_photo_path)
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
        except Exception as save_error:
            QMessageBox.critical(self, "Ошибка", str(save_error))

    def _show_photo(self, path=None):
        """Показывает в форме текущее фото: новое загруженное, по пути из БД или заглушку."""
        path_candidates = [self.new_photo_path]
        if path:
            path_candidates.append(_resolve_product_photo_path(path))
            path_candidates.append(os.path.join(ROOT, path))
        for file_path in path_candidates:
            if file_path and os.path.isfile(file_path):
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():
                    self.photo_label.setPixmap(pixmap.scaled(IMAGE_MAX_WIDTH, IMAGE_MAX_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                    return
        self.photo_label.setPixmap(_placeholder_pixmap())
