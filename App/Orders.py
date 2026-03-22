from PySide6.QtWidgets import (
    QTableWidgetItem,
    QMessageBox,
    QHeaderView,
    QAbstractItemView,
    QSizePolicy,
    QComboBox,
)
from PySide6.QtCore import Qt
from PySide6.QtUiTools import loadUiType

from App.config import UI, ROLE_ADMINISTRATOR
from logic.order_list import load_orders, delete_order
from logic.order_edit import get_order_statuses

Ui_Orders, BaseOrders = loadUiType(UI["orders"])

def _normalize_role(role_name):
    value = (role_name or "").strip().lower()
    if value in ("administrator", "администратор", "admin"):
        return ROLE_ADMINISTRATOR
    return value


class Orders(BaseOrders, Ui_Orders):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.user = user
        self.role = _normalize_role(user.get("role_name") or user.get("role") or "guest")
        self.edit_open = False

        self.setWindowTitle("Заказы")
        self.lbl_user.setText(user.get("full_name", "Гость"))

        self._setup_ui()
        self._connect_signals()
        self._refresh()

    def _setup_ui(self):
        is_admin = self.role == ROLE_ADMINISTRATOR

        self.lbl_user.setWordWrap(True)
        self.btn_add.setVisible(is_admin)
        self.btn_del.setVisible(is_admin)

        table = self.table
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def _connect_signals(self):
        self.btn_back.clicked.connect(self.close)

        if self.role == ROLE_ADMINISTRATOR:
            self.btn_add.clicked.connect(self._on_add_order_clicked)
            self.btn_del.clicked.connect(self._delete)
            self.table.cellDoubleClicked.connect(self._open_from_table)

    def _on_add_order_clicked(self):
        self._open_form(None)

    def _refresh(self):
        orders = load_orders()

        statuses = get_order_statuses()
        table = self.table
        table.setRowCount(len(orders))

        for row_index, order in enumerate(orders):
            values = [
                str(order.get("pickup_code", "")),
                order.get("status_name") or "",
                (order.get("pickup_point_address") or "")[:80],
                str(order.get("order_date") or ""),
                str(order.get("delivery_date") or ""),
            ]

            for column_index, value in enumerate(values):
                if column_index == 1:
                    cb = QComboBox()
                    cb.addItems(statuses)
                    cb.setEnabled(False)
                    i = cb.findText(value)
                    if i >= 0:
                        cb.setCurrentIndex(i)
                    else:
                        cb.setCurrentText(value)
                    table.setCellWidget(row_index, column_index, cb)
                else:
                    table.setItem(row_index, column_index, QTableWidgetItem(value))

            table.item(row_index, 0).setData(Qt.ItemDataRole.UserRole, order.get("id"))

    def _get_selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _open_form(self, order_id):
        if self.edit_open:
            return

        from App.OrderForm import OrderForm

        self.edit_open = True
        order_form_window = OrderForm(order_id, self)

        order_form_window.setWindowModality(Qt.WindowModality.WindowModal)
        order_form_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        order_form_window.destroyed.connect(self._on_order_form_destroyed)
        order_form_window.accepted.connect(self._refresh)

        order_form_window.show()

    def _on_order_form_destroyed(self, *args):
        self.edit_open = False

    def _open_from_table(self, row, _):
        item = self.table.item(row, 0)
        if item:
            order_id = item.data(Qt.ItemDataRole.UserRole)
            if order_id:
                self._open_form(order_id)

    def _delete(self):
        order_id = self._get_selected_id()
        delete_order(order_id)
        self._refresh()
