# OrderForm.py
from datetime import date

from PySide6.QtCore import Signal, QDate
from PySide6.QtWidgets import QMessageBox
from PySide6.QtUiTools import loadUiType

from App.config import ui_path
from App.db import format_order_items_line, get_order_by_id, get_order_statuses, get_pickup_points, save_order

Ui_OrderForm, BaseOrderForm = loadUiType(ui_path("order"))


class OrderForm(BaseOrderForm, Ui_OrderForm):
    accepted = Signal()

    def __init__(self, order_id, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.order_id = order_id
        self.edit = bool(order_id)
        self._uid = None

        self.setWindowTitle("Заказ" if self.edit else "Новый заказ")
        self.status_combo.clear()
        self.status_combo.addItems(get_order_statuses())
        self.pickup_combo.clear()
        self.pickup_combo.addItem("(не выбран)", None)
        for p in get_pickup_points():
            self.pickup_combo.addItem(p["pickup_address"], p["pickup_point_id"])
        for w in (self.order_date_edit, self.delivery_date_edit):
            w.setCalendarPopup(True)
            w.setDate(date.today())
        if not self.edit:
            self.id_edit.hide()
            self.lbl_id.hide()

        self.btn_save.clicked.connect(self._save)
        self.btn_cancel.clicked.connect(self.reject)

        if self.edit:
            o = get_order_by_id(self.order_id)
            self.id_edit.setText(str(o["id"]))
            self.article_edit.setPlainText(format_order_items_line(o.get("items") or []))
            self.receiver_edit.setText(str(o.get("receiver_code") or ""))
            self.client_edit.setText(str(o.get("client_name") or ""))
            i = self.status_combo.findText(o.get("status_name") or "")
            if i >= 0:
                self.status_combo.setCurrentIndex(i)
            pp = o.get("pickup_point_id")
            if pp is not None:
                j = self.pickup_combo.findData(pp)
                if j >= 0:
                    self.pickup_combo.setCurrentIndex(j)
            for key, w in (("order_date", self.order_date_edit), ("delivery_date", self.delivery_date_edit)):
                v = o.get(key)
                if v:
                    d = date.fromisoformat(str(v)[:10])
                    w.setDate(QDate(d.year, d.month, d.day))

    def _save(self):
        try:
            save_order(
                self.order_id if self.edit else None,
                {
                    "status_name": self.status_combo.currentText().strip(),
                    "pickup_point_id": self.pickup_combo.currentData(),
                    "product_article": self.article_edit.toPlainText().strip(),
                    "order_date": self.order_date_edit.date().toPython(),
                    "delivery_date": self.delivery_date_edit.date().toPython(),
                    "receiver_code": self.receiver_edit.text().strip() or None,
                    "user_name": self.client_edit.text().strip() or None,
                },
            )
        except ValueError as e:
            QMessageBox.warning(self, "Заказ", str(e))
            return
        self.accepted.emit()
        self.accept()
