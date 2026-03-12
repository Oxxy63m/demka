# Диалог оформления заказа (корзина): таблица товаров, пункт выдачи, дата доставки, кнопки «Оформить» и «Отмена». Разметка — ui/cart.ui.
from datetime import date
from PySide6.QtWidgets import QDialog, QMessageBox, QTableWidgetItem, QAbstractItemView
from PySide6.QtCore import Qt
from PySide6.QtUiTools import loadUiType

from App.config import UI
from App.db import get_order_statuses, get_pickup_addresses, insert_order, insert_order_items

Ui_Cart, BaseCart = loadUiType(UI["cart"])


class Cart(BaseCart, Ui_Cart):
    def __init__(self, user, cart_items, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.user = user
        self.cart_items = list(cart_items)  # [{"product_id", "product_name", "price", "quantity"}, ...]
        self.setWindowTitle("Оформление заказа")
        self.lbl_title.setStyleSheet("font-weight: bold;")
        self.table_items.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_items.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        for pt in get_pickup_addresses():
            self.cb_pickup.addItem(pt)
        self.de_delivery.setCalendarPopup(True)
        self.de_delivery.setDate(date.today())
        self._fill_table()
        self._update_total()
        self.btn_remove.clicked.connect(self._remove_selected)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_confirm.clicked.connect(self._confirm_order)

    def _fill_table(self):
        self.table_items.setRowCount(len(self.cart_items))
        for row, it in enumerate(self.cart_items):
            self.table_items.setItem(row, 0, QTableWidgetItem(it.get("product_name", "")))
            self.table_items.setItem(row, 1, QTableWidgetItem(str(it.get("quantity", 0))))
            price = float(it.get("price", 0))
            qty = int(it.get("quantity", 0))
            self.table_items.setItem(row, 2, QTableWidgetItem(f"{price:.2f}"))
            self.table_items.setItem(row, 3, QTableWidgetItem(f"{price * qty:.2f}"))

    def _update_total(self):
        total = sum(
            float(it.get("price", 0)) * int(it.get("quantity", 0))
            for it in self.cart_items
        )
        self.lbl_total.setText(f"{total:.2f} ₽")

    def _remove_selected(self):
        row = self.table_items.currentRow()
        if row < 0 or row >= len(self.cart_items):
            return
        self.cart_items.pop(row)
        self._fill_table()
        self._update_total()

    def _confirm_order(self):
        if not self.cart_items:
            QMessageBox.warning(self, "Внимание", "Корзина пуста.")
            return
        user_id = self.user.get("user_id") or self.user.get("id")
        if not user_id:
            QMessageBox.warning(self, "Ошибка", "Не указан пользователь.")
            return
        try:
            items = [
                {"product_id": it["product_id"], "quantity": int(it.get("quantity", 1)), "unit_price": float(it.get("price", 0))}
                for it in self.cart_items
            ]
            statuses = get_order_statuses()
            addresses = get_pickup_addresses()
            order_data = {
                "order_date": date.today(),
                "delivery_date": self.de_delivery.date().toPython(),
                "pickup_point": self.cb_pickup.currentText().strip() or (addresses[0] if addresses else ""),
                "user_id": user_id,
                "status": statuses[0] if statuses else "новый",
            }
            order_id = insert_order(order_data)
            insert_order_items(order_id, items)
            QMessageBox.information(self, "Готово", "Заказ оформлен.")
            self.accept()
        except Exception as error:
            QMessageBox.critical(self, "Ошибка", str(error))
