from datetime import date

from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import Signal, QDate
from PySide6.QtUiTools import loadUiType

from App.config import UI
from logic.order_edit import load_order, save_order, get_order_statuses

Ui_OrderForm, BaseOrderForm = loadUiType(UI["order"])


class OrderForm(BaseOrderForm, Ui_OrderForm):
    accepted = Signal()

    def __init__(self, order_id, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.order_id = order_id
        self.is_edit = bool(order_id)
        self.user = parent.user
        self.fixed_user_id = self.user.get("user_id") or self.user.get("id")
        self.order_user_id = None

        self.setWindowTitle("Редактирование заказа" if self.is_edit else "Добавление заказа")

        self._setup_ui()
        self._connect_signals()

        if self.is_edit:
            self._load()

    def _setup_ui(self):
        self.pickup_edit.setPlaceholderText("Адрес пункта выдачи")
        self.article_edit.setPlaceholderText("Артикул, количество, артикул, количество…")

        self.status_combo.clear()
        self.status_combo.addItems(get_order_statuses())
        self.user_combo.hide()
        self.lbl_user.hide()

        for w in (self.order_date_edit, self.delivery_date_edit):
            w.setCalendarPopup(True)
            w.setDate(date.today())

        if not self.is_edit:
            self.id_edit.hide()
            self.lbl_id.hide()

    def _connect_signals(self):
        self.btn_save.clicked.connect(self._save)
        self.btn_cancel.clicked.connect(self.reject)

    def _load(self):
        o = load_order(self.order_id)

        if not o:
            self.reject()
            return

        self.id_edit.setText(str(o.get("id", "")))
        self.order_user_id = o.get("user_id")
        self.pickup_edit.setText(o.get("pickup_point_address") or "")
        self.article_edit.setText(o.get("pickup_code") or "")

        i = self.status_combo.findText(o.get("status_name") or "")
        if i >= 0:
            self.status_combo.setCurrentIndex(i)

        for key, w in (("order_date", self.order_date_edit), ("delivery_date", self.delivery_date_edit)):
            v = o.get(key)
            if v:
                d = date.fromisoformat(str(v)[:10])
                w.setDate(QDate(d.year, d.month, d.day))

    def _save(self):
        if self.is_edit:
            user_id = self.order_user_id
        else:
            user_id = self.fixed_user_id

        pickup_code = self.article_edit.text().strip()

        statuses = get_order_statuses()
        data = {
            "status": self.status_combo.currentText().strip() or (statuses[0] if statuses else ""),
            "pickup_point": self.pickup_edit.text().strip(),
            "pickup_code": pickup_code,
            "order_date": self.order_date_edit.date().toPython(),
            "delivery_date": self.delivery_date_edit.date().toPython(),
            "user_id": user_id,
        }

        try:
            save_order(self.order_id if self.is_edit else None, data)
        except ValueError as e:
            QMessageBox.warning(self, "Код заказа", str(e))
            return

        self.accepted.emit()
        self.accept()
