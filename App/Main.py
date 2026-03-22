# Main.py
from PySide6.QtCore import Qt
from PySide6.QtUiTools import loadUiType

from App.config import is_admin_role, is_manager_or_admin, role_title_ru, ui_path
from App.db import delete_product, get_products_all, get_supplier_names
from App.Card import Card

Ui_Main, BaseMain = loadUiType(ui_path("main"))


class Main(BaseMain, Ui_Main):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.user = user
        self.role = str(user.get("role_name") or "guest").strip().lower()

        self.setWindowTitle("Список товаров")
        self.lbl_user.setText((user.get("full_name") or "").strip() or "—")
        self.lbl_role.setText(role_title_ru(self.role))

        is_admin = is_admin_role(self.role)
        is_mgr = is_manager_or_admin(self.role)

        self.btn_add.setVisible(is_admin)
        self.btn_orders.setVisible(is_mgr)
        self.lbl_search.setVisible(is_mgr)
        self.search_edit.setVisible(is_mgr)
        self.lbl_supplier.setVisible(is_mgr)
        self.supplier_combo.setVisible(is_mgr)
        self.lbl_sort.setVisible(is_mgr)
        self.sort_combo.setVisible(is_mgr)

        if is_mgr:
            self.supplier_combo.clear()
            self.supplier_combo.addItem("Все", None)
            for s in get_supplier_names():
                self.supplier_combo.addItem(s, s)
            self.sort_combo.clear()
            self.sort_combo.addItem("—", None)
            self.sort_combo.addItem("По возрастанию", "asc")
            self.sort_combo.addItem("По убыванию", "desc")

        self.btn_logout.clicked.connect(self.close)
        self.btn_orders.clicked.connect(self._open_orders)
        if is_mgr:
            self.search_edit.textChanged.connect(self._refresh_product_list)
            self.supplier_combo.currentIndexChanged.connect(self._refresh_product_list)
            self.sort_combo.currentIndexChanged.connect(self._refresh_product_list)
        if is_admin:
            self.btn_add.clicked.connect(lambda: self._open_product_form(None))

        self._refresh_product_list()

    def _delete_product(self, pid):
        delete_product(pid)
        self._refresh_product_list()

    def _refresh_product_list(self):
        search = self.search_edit.text().strip() if self.search_edit.isVisible() else ""
        sup = self.supplier_combo.currentData() if self.supplier_combo.isVisible() else None
        sort_q = self.sort_combo.currentData() if self.sort_combo.isVisible() else None
        items = get_products_all(search, sup, sort_q)

        lay = self.cards_layout
        while lay.count():
            it = lay.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()

        adm = is_admin_role(self.role)
        for p in items:
            c = Card(p, is_admin=adm)
            if adm:
                c.clicked.connect(self._open_product_form)
                c.delete_requested.connect(self._delete_product)
            lay.addWidget(c)
        lay.addStretch()

    def _open_orders(self):
        from App.Orders import Orders

        w = Orders(self.user, parent=self)
        w.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        w.showMaximized()

    def _open_product_form(self, product_id):
        from App.ProdForm import ProdForm

        f = ProdForm(product_id, self)
        f.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        f.accepted.connect(self._refresh_product_list)
        f.show()

