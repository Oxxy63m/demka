import os
import sys

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QTextEdit, QPushButton,
    QFileDialog, QMessageBox, QGroupBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QImage

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import IMAGES_FOLDER, IMAGE_MAX_WIDTH, IMAGE_MAX_HEIGHT, PLACEHOLDER_IMAGE
from database.db import get_product_by_id, insert_product, update_product

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def placeholder():
    path = os.path.join(ROOT, "resources", PLACEHOLDER_IMAGE)
    if os.path.isfile(path):
        pix = QPixmap(path)
        if not pix.isNull():
            return pix.scaled(IMAGE_MAX_WIDTH, IMAGE_MAX_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    pix = QPixmap(IMAGE_MAX_WIDTH, IMAGE_MAX_HEIGHT)
    pix.fill(Qt.GlobalColor.lightGray)
    return pix


def save_image(path):
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


class ProductEditWindow(QDialog):
    accepted = Signal()

    def __init__(self, product_id, parent=None):
        super().__init__(parent)
        self.product_id = product_id
        self.is_edit = product_id is not None
        self.new_photo_path = None
        self.old_photo_path = None
        self.setWindowTitle("Редактирование товара" if self.is_edit else "Добавление товара")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        row = QHBoxLayout()
        row.addWidget(QLabel("ID:"))
        self.id_edit = QLineEdit()
        self.id_edit.setReadOnly(True)
        if self.is_edit:
            row.addWidget(self.id_edit)
        else:
            row.addWidget(QLabel("(новый)"))
        layout.addLayout(row)

        photo_group = QGroupBox("Фото")
        photo_layout = QVBoxLayout(photo_group)
        self.photo_label = QLabel()
        self.photo_label.setFixedSize(IMAGE_MAX_WIDTH, IMAGE_MAX_HEIGHT)
        self.photo_label.setStyleSheet("border:1px solid #ccc;background:#f0f0f0")
        photo_layout.addWidget(self.photo_label, alignment=Qt.AlignmentFlag.AlignCenter)
        btn_photo = QPushButton("Добавить / заменить изображение")
        btn_photo.clicked.connect(self.load_photo)
        photo_layout.addWidget(btn_photo)
        layout.addWidget(photo_group)

        form = QFormLayout()
        self.article_edit = QLineEdit()
        self.article_edit.setPlaceholderText("Артикул товара")
        form.addRow("Артикул:", self.article_edit)
        self.name_edit = QLineEdit()
        form.addRow("Наименование:", self.name_edit)
        self.category_edit = QLineEdit()
        form.addRow("Категория:", self.category_edit)
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(70)
        form.addRow("Описание:", self.desc_edit)
        self.manuf_edit = QLineEdit()
        form.addRow("Производитель:", self.manuf_edit)
        self.supp_edit = QLineEdit()
        form.addRow("Поставщик:", self.supp_edit)
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, 999999.99)
        self.price_spin.setDecimals(2)
        form.addRow("Цена:", self.price_spin)
        self.unit_edit = QLineEdit()
        self.unit_edit.setPlaceholderText("шт.")
        form.addRow("Ед. изм.:", self.unit_edit)
        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(0, 999999)
        form.addRow("Кол-во:", self.qty_spin)
        self.discount_spin = QDoubleSpinBox()
        self.discount_spin.setRange(0, 100)
        self.discount_spin.setDecimals(2)
        form.addRow("Скидка %:", self.discount_spin)
        layout.addLayout(form)

        row = QHBoxLayout()
        btn_save = QPushButton("Сохранить")
        btn_save.clicked.connect(self.save)
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)
        row.addWidget(btn_save)
        row.addWidget(btn_cancel)
        layout.addLayout(row)

        if self.is_edit:
            self.load_product()
        else:
            self.photo_label.setPixmap(placeholder())

    def show_photo(self, path=None):
        candidates = [self.new_photo_path, os.path.join(ROOT, path) if path else None]
        for file_path in candidates:
            if file_path and os.path.isfile(file_path):
                pix = QPixmap(file_path)
                if not pix.isNull():
                    self.photo_label.setPixmap(pix.scaled(IMAGE_MAX_WIDTH, IMAGE_MAX_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                    return
        self.photo_label.setPixmap(placeholder())

    def load_product(self):
        try:
            product = get_product_by_id(self.product_id)
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
        self.category_edit.setText(product.get("category") or "")
        self.desc_edit.setPlainText(product.get("description") or "")
        self.manuf_edit.setText(product.get("manufacturer") or "")
        self.supp_edit.setText(product.get("supplier") or "")
        self.price_spin.setValue(float(product.get("price") or 0))
        self.unit_edit.setText(product.get("unit") or "")
        self.qty_spin.setValue(int(product.get("stock_quantity") or 0))
        self.discount_spin.setValue(float(product.get("discount") or 0))
        self.old_photo_path = product.get("photo")
        self.show_photo(self.old_photo_path)

    def load_photo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите изображение", "", "Изображения (*.png *.jpg *.jpeg)")
        if not path:
            return
        if QPixmap(path).isNull():
            QMessageBox.warning(self, "Ошибка", "Не удалось открыть файл.")
            return
        self.new_photo_path = path
        self.show_photo()

    def save(self):
        article = self.article_edit.text().strip()
        product_name = self.name_edit.text().strip()
        if not product_name:
            QMessageBox.warning(self, "Ошибка", "Введите наименование.")
            return
        if self.price_spin.value() < 0 or self.qty_spin.value() < 0:
            QMessageBox.warning(self, "Ошибка", "Цена и количество не могут быть отрицательными.")
            return

        photo = self.old_photo_path
        if self.new_photo_path:
            photo = save_image(self.new_photo_path)
            if not photo:
                QMessageBox.warning(self, "Ошибка", "Не удалось сохранить изображение.")
                return
            if self.is_edit and self.old_photo_path:
                old_full = os.path.join(ROOT, self.old_photo_path)
                if os.path.isfile(old_full):
                    try:
                        os.remove(old_full)
                    except OSError:
                        pass

        data = {
            "article": article,
            "product_name": product_name,
            "category": self.category_edit.text().strip(),
            "description": self.desc_edit.toPlainText().strip(),
            "manufacturer": self.manuf_edit.text().strip(),
            "supplier": self.supp_edit.text().strip(),
            "price": self.price_spin.value(),
            "unit": self.unit_edit.text().strip() or "шт.",
            "stock_quantity": self.qty_spin.value(),
            "discount": self.discount_spin.value(),
            "photo": photo,
        }
        try:
            if self.is_edit:
                update_product(self.product_id, data)
                QMessageBox.information(self, "Готово", "Товар обновлён.")
            else:
                insert_product(data)
                QMessageBox.information(self, "Готово", "Товар добавлен.")
            self.accepted.emit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
