# App/Orders.py — окно списка заказов, разметка из UI/orders_list.ui
from PySide6.QtWidgets import QMainWindow, QTableWidgetItem, QMessageBox, QHeaderView, QAbstractItemView, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtUiTools import loadUiType

from App.config import UI, ROLE_ADMINISTRATOR
from logic.order_list import load_orders, delete_order

Ui_Orders, BaseOrders = loadUiType(UI["orders"])


class Orders(BaseOrders, Ui_Orders):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.user = user
        self.role = user.get("role", "guest")
        self.edit_open = False
        self.setWindowTitle("Заказы")
        self.lbl_user.setWordWrap(True)
        self.lbl_user.setText(user.get("full_name", "Гость"))
        self.btn_back.clicked.connect(self.close)
        if self.role != ROLE_ADMINISTRATOR:
            self.btn_add.setVisible(False)
            self.btn_del.setVisible(False)
        else:
            self.btn_add.clicked.connect(self._on_add)
            self.btn_del.clicked.connect(self._on_delete)
            self.table.cellDoubleClicked.connect(self._on_edit)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._refresh()

    def _refresh(self):
        try:
            rows = load_orders()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            return
        self.table.setRowCount(len(rows))
        for i, order in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(order.get("order_article") or ""))
            self.table.setItem(i, 1, QTableWidgetItem(order.get("status") or ""))
            self.table.setItem(i, 2, QTableWidgetItem((order.get("pickup_point") or "")[:80]))
            self.table.setItem(i, 3, QTableWidgetItem(str(order.get("order_date") or "")))
            self.table.setItem(i, 4, QTableWidgetItem(str(order.get("delivery_date") or "")))
            self.table.setItem(i, 5, QTableWidgetItem(order.get("user_name") or ""))
            self.table.item(i, 0).setData(Qt.ItemDataRole.UserRole, order.get("id"))

    def _current_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        it = self.table.item(row, 0)
        return it.data(Qt.ItemDataRole.UserRole) if it else None

    def _open_edit(self, order_id):
        if self.edit_open:
            QMessageBox.warning(self, "Предупреждение", "Закройте окно редактирования заказа.")
            return
        from App.OrderForm import OrderForm
        self.edit_open = True
        w = OrderForm(order_id, self)
        w.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        w.destroyed.connect(lambda: setattr(self, "edit_open", False))
        w.accepted.connect(self._refresh)
        w.show()

    def _on_add(self):
        self._open_edit(None)

    def _on_edit(self, row, col):
        it = self.table.item(row, 0)
        if it:
            oid = it.data(Qt.ItemDataRole.UserRole)
            if oid:
                self._open_edit(oid)

    def _on_delete(self):
        oid = self._current_id()
        if not oid:
            QMessageBox.warning(self, "Ошибка", "Выберите заказ.")
            return
        if QMessageBox.question(
            self, "Подтверждение", "Удалить заказ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return
        try:
            delete_order(oid)
            QMessageBox.information(self, "Готово", "Заказ удалён.")
            self._refresh()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
