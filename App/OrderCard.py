# OrderCard.py
from PySide6.QtWidgets import QFrame
from PySide6.QtCore import Qt, Signal
from PySide6.QtUiTools import loadUiType

from App.config import UI

Ui_OrderCard, BaseOrderCard = loadUiType(UI["order_card"])


class OrderCard(BaseOrderCard, Ui_OrderCard):
    selected = Signal(int)
    open_requested = Signal(int)

    def __init__(self, order, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.order_id = order.get("id")

        self.lbl_order_article.setText("Артикул заказа: " + str(order.get("article") or ""))
        self.lbl_order_article.setStyleSheet("font-weight: bold;")
        self.lbl_status.setText("Статус заказа: " + str(order.get("status_name") or ""))
        self.lbl_pickup_address.setText("Адрес пункта выдачи: " + str(order.get("pickup_point_address") or ""))
        self.lbl_order_date.setText("Дата заказа: " + str(order.get("order_date") or ""))
        self.lbl_delivery_date.setText("Дата доставки\n" + str(order.get("delivery_date") or ""))
        for w in (
            self.lbl_order_article,
            self.lbl_status,
            self.lbl_pickup_address,
            self.lbl_order_date,
            self.lbl_delivery_date,
        ):
            w.setWordWrap(True)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self.order_id is not None:
            self.selected.emit(self.order_id)
        super().mousePressEvent(e)

    def mouseDoubleClickEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self.order_id is not None:
            self.open_requested.emit(self.order_id)
        super().mouseDoubleClickEvent(e)
