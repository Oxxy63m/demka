# Форма добавления и редактирования заказа: даты, пункт выдачи, статус, клиент. Разметка — ui/order_form.ui.
from datetime import date
from PySide6.QtWidgets import QDialog, QMessageBox
from PySide6.QtCore import Signal, QDate
from PySide6.QtUiTools import loadUiType

from App.config import UI
from logic.order_edit import load_order, save_order, get_order_statuses, get_users_list

Ui_OrderForm, BaseOrderForm = loadUiType(UI["order"])


class OrderForm(BaseOrderForm, Ui_OrderForm):
    accepted = Signal()

    def __init__(self, order_id, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.order_id = order_id
        self.is_edit = order_id is not None
        self.setWindowTitle("Редактирование заказа" if self.is_edit else "Добавление заказа")
        self.article_edit.setPlaceholderText("Артикул заказа")
        self.pickup_edit.setPlaceholderText("Адрес пункта выдачи")
        for status_text in get_order_statuses():
            self.status_combo.addItem(status_text)
        users_list = get_users_list()
        for user_record in users_list:
            self.user_combo.addItem(user_record.get("full_name", ""), user_record.get("user_id"))
        if not users_list:
            self.user_combo.addItem("—", None)
        self.order_date_edit.setCalendarPopup(True)
        self.order_date_edit.setDate(date.today())
        self.delivery_date_edit.setCalendarPopup(True)
        self.delivery_date_edit.setDate(date.today())
        self.left_group.setStyleSheet(
            "QGroupBox { font-weight: bold; background-color: #E8F5E9; border: 1px solid #2E8B57; border-radius: 4px; margin-top: 8px; padding-top: 8px; } QGroupBox::title { color: #2E8B57; }"
        )
        self.right_group.setStyleSheet(
            "QGroupBox { font-weight: bold; background-color: #E3F2FD; border: 1px solid #ADD8E6; border-radius: 4px; margin-top: 8px; padding-top: 8px; } QGroupBox::title { color: #1976D2; }"
        )
        if not self.is_edit:
            self.id_edit.setVisible(False)
            self.lbl_id.setVisible(False)
        self.btn_save.clicked.connect(self._save)
        self.btn_cancel.clicked.connect(self.reject)
        if self.is_edit:
            self._load_order()
        else:
            if self.user_combo.count() and self.user_combo.findData(None) < 0:
                self.user_combo.setCurrentIndex(0)

    def _load_order(self):
        try:
            order = load_order(self.order_id)
        except Exception as load_error:
            QMessageBox.critical(self, "Ошибка", str(load_error))
            self.reject()
            return
        if not order:
            self.reject()
            return
        self.id_edit.setText(str(order.get("id", "")))
        self.article_edit.setText(order.get("order_article") or "")
        status_index = self.status_combo.findText(order.get("status") or "")
        if status_index >= 0:
            self.status_combo.setCurrentIndex(status_index)
        self.pickup_edit.setText(order.get("pickup_point") or "")
        for date_field_name, date_edit_widget in (("order_date", self.order_date_edit), ("delivery_date", self.delivery_date_edit)):
            date_value = order.get(date_field_name)
            if date_value:
                date_object = date_value if hasattr(date_value, "year") else date.fromisoformat(str(date_value)[:10])
                date_edit_widget.setDate(QDate(date_object.year, date_object.month, date_object.day))
        user_index = self.user_combo.findData(order.get("user_id"))
        if user_index >= 0:
            self.user_combo.setCurrentIndex(user_index)

    def _save(self):
        """Проверяет выбор клиента и сохраняет заказ в БД (добавление или обновление), затем закрывает форму."""
        user_id = self.user_combo.currentData()
        if user_id is None and self.user_combo.count():
            user_id = self.user_combo.itemData(0)
        if user_id is None:
            QMessageBox.warning(self, "Ошибка", "Выберите клиента.")
            return
        data = {
            "order_article": self.article_edit.text().strip(),
            "status": self.status_combo.currentText().strip() or get_order_statuses()[0],
            "pickup_point": self.pickup_edit.text().strip(),
            "order_date": self.order_date_edit.date().toPython(),
            "delivery_date": self.delivery_date_edit.date().toPython(),
            "user_id": user_id,
        }
        try:
            save_order(self.order_id if self.is_edit else None, data)
            QMessageBox.information(self, "Готово", "Заказ обновлён." if self.is_edit else "Заказ добавлен.")
            self.accepted.emit()
            self.accept()
        except Exception as save_error:
            QMessageBox.critical(self, "Ошибка", str(save_error))
