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
            self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._refresh_orders_table()

    def _refresh_orders_table(self):
        try:
            orders_list = load_orders()
        except Exception as load_error:
            QMessageBox.critical(self, "Ошибка", str(load_error))
            return
        self.table.setRowCount(len(orders_list))
        for row_index, order in enumerate(orders_list):
            self.table.setItem(row_index, 0, QTableWidgetItem(order.get("order_article") or ""))
            self.table.setItem(row_index, 1, QTableWidgetItem(order.get("status") or ""))
            self.table.setItem(row_index, 2, QTableWidgetItem((order.get("pickup_point") or "")[:80]))
            self.table.setItem(row_index, 3, QTableWidgetItem(str(order.get("order_date") or "")))
            self.table.setItem(row_index, 4, QTableWidgetItem(str(order.get("delivery_date") or "")))
            self.table.setItem(row_index, 5, QTableWidgetItem(order.get("user_name") or ""))
            self.table.item(row_index, 0).setData(Qt.ItemDataRole.UserRole, order.get("id"))

    def _get_selected_order_id(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            return None
        first_column_item = self.table.item(current_row, 0)
        return first_column_item.data(Qt.ItemDataRole.UserRole) if first_column_item else None

    def _open_order_edit_form(self, order_id):
        if self.edit_open:
            QMessageBox.warning(self, "Предупреждение", "Закройте окно редактирования заказа.")
            return
        from App.OrderForm import OrderForm
        self.edit_open = True
        order_form_window = OrderForm(order_id, self)
        order_form_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        order_form_window.destroyed.connect(lambda: setattr(self, "edit_open", False))
        order_form_window.accepted.connect(self._refresh_orders_table)
        order_form_window.show()

    def _on_add(self):
        self._open_order_edit_form(None)

    def _on_cell_double_clicked(self, row_index, column_index):
        first_column_item = self.table.item(row_index, 0)
        if first_column_item:
            selected_order_id = first_column_item.data(Qt.ItemDataRole.UserRole)
            if selected_order_id:
                self._open_order_edit_form(selected_order_id)

    def _on_delete(self):
        selected_order_id = self._get_selected_order_id()
        if not selected_order_id:
            QMessageBox.warning(self, "Ошибка", "Выберите заказ.")
            return
        if QMessageBox.question(
            self, "Подтверждение", "Удалить заказ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return
        try:
            delete_order(selected_order_id)
            QMessageBox.information(self, "Готово", "Заказ удалён.")
            self._refresh_orders_table()
        except Exception as delete_error:
            QMessageBox.critical(self, "Ошибка", str(delete_error))
