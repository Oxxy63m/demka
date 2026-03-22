# Orders.py
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtUiTools import loadUiType

from App.config import is_admin_role, role_title_ru, ui_path
from App.db import delete_order, get_orders_all
from App.OrderCard import OrderCard

Ui_Orders, BaseOrders = loadUiType(ui_path("orders"))


class Orders(BaseOrders, Ui_Orders):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.user = user
        self.role = str(user.get("role_name") or "").strip().lower()
        self._sel = None

        self.lbl_user.setText((user.get("full_name") or "").strip() or "—")
        self.lbl_role.setText(role_title_ru(self.role))
        adm = is_admin_role(self.role)
        self.btn_add.setVisible(adm)
        self.btn_del.setVisible(adm)
        self.orders_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.btn_back.clicked.connect(self.close)
        if adm:
            self.btn_add.clicked.connect(lambda: self._open(None))
            self.btn_del.clicked.connect(self._delete)

        self._fill()

    def _fill(self):
        lay = self.orders_cards_layout
        while lay.count():
            it = lay.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()
        self._sel = None
        for o in get_orders_all():
            c = OrderCard(o, parent=self.orders_scroll_contents)
            c.selected.connect(self._on_sel)
            if is_admin_role(self.role):
                c.open_requested.connect(self._open)
            lay.addWidget(c)
        lay.addStretch()

    def _on_sel(self, oid):
        self._sel = oid

    def _open(self, oid):
        from App.OrderForm import OrderForm

        f = OrderForm(oid, self)
        f.setWindowModality(Qt.WindowModality.WindowModal)
        f.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        f.accepted.connect(self._fill)
        f.show()

    def _delete(self):
        if self._sel:
            delete_order(self._sel)
            self._fill()
