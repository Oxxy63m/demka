from PySide6.QtWidgets import QMessageBox, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtUiTools import loadUiType

from App.config import UI, ROLE_MANAGER, ROLE_ADMINISTRATOR, ROLE_CLIENT, ROLE_GUEST
from App.Card import Card
from logic.product_list import load_products, get_supplier_names, product_in_orders, delete_product

Ui_Main, BaseMain = loadUiType(UI["main"])

def _normalize_role(role_name):
    value = (role_name or "").strip().lower()
    if value in ("administrator", "администратор", "admin"):
        return ROLE_ADMINISTRATOR
    if value in ("manager", "менеджер"):
        return ROLE_MANAGER
    if value in ("client", "клиент"):
        return ROLE_CLIENT
    if value in ("guest", "гость"):
        return ROLE_GUEST
    return value or ROLE_GUEST


class Main(BaseMain, Ui_Main):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.user = user
        self.role = _normalize_role(user.get("role_name") or user.get("role") or ROLE_GUEST)
        self.edit_open = False

        self.setWindowTitle(f"Список товаров ({self.role})")
        self.lbl_user.setText(user.get("full_name", "Гость"))

        self._setup_ui()
        self._connect_signals()
        self.cards_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._refresh_product_list()

    def _setup_ui(self):
        is_admin = self.role == ROLE_ADMINISTRATOR
        is_manager = self.role in (ROLE_MANAGER, ROLE_ADMINISTRATOR)

        self.btn_add.setVisible(is_admin)
        self.btn_orders.setVisible(self.role in (ROLE_MANAGER, ROLE_ADMINISTRATOR))

        self.lbl_search.setVisible(is_manager)
        self.search_edit.setVisible(is_manager)
        self.lbl_supplier.setVisible(is_manager)
        self.supplier_combo.setVisible(is_manager)
        self.lbl_sort.setVisible(is_manager)
        self.sort_combo.setVisible(is_manager)

        if is_manager:
            self.supplier_combo.clear()
            self.supplier_combo.addItem("Все поставщики", None)
            for supplier_name in get_supplier_names():
                self.supplier_combo.addItem(supplier_name, supplier_name)

            self.sort_combo.clear()
            self.sort_combo.addItem("—", None)
            self.sort_combo.addItem("По возрастанию кол-ва", "asc")
            self.sort_combo.addItem("По убыванию кол-ва", "desc")

    def _connect_signals(self):
        self.btn_logout.clicked.connect(self.close)
        self.btn_orders.clicked.connect(self._open_orders)

        if self.role in (ROLE_MANAGER, ROLE_ADMINISTRATOR):
            self.search_edit.textChanged.connect(self._refresh_product_list)
            self.supplier_combo.currentIndexChanged.connect(self._refresh_product_list)
            self.sort_combo.currentIndexChanged.connect(self._refresh_product_list)

        if self.role == ROLE_ADMINISTRATOR:
            self.btn_add.clicked.connect(self._on_add_product_clicked)

    def _on_add_product_clicked(self):
        self._open_product_form(None)

    def _refresh_product_list(self):
        search_text = self.search_edit.text().strip()
        supplier_filter = self.supplier_combo.currentData()
        sort_by_quantity = self.sort_combo.currentData()
        product_list = load_products(search_text, supplier_filter, sort_by_quantity)
        while self.cards_layout.count():
            layout_item = self.cards_layout.takeAt(0)
            if layout_item.widget():
                layout_item.widget().deleteLater()
        user_is_administrator = self.role == ROLE_ADMINISTRATOR
        for product in product_list:
            card = Card(product, is_admin=user_is_administrator, is_client=False)
            if user_is_administrator:
                card.clicked.connect(self._open_product_form)
                card.delete_requested.connect(self._delete_product)
            self.cards_layout.addWidget(card)

    def _open_orders(self):
        from App.Orders import Orders

        self._orders_window = Orders(self.user, parent=self)
        self._orders_window.setWindowModality(Qt.WindowModality.WindowModal)
        self._orders_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self._orders_window.showMaximized()

    def _open_product_form(self, product_id):
        if self.edit_open:
            return
        from App.ProdForm import ProdForm
        self.edit_open = True

        product_form_window = ProdForm(product_id, self)
        product_form_window.setWindowModality(Qt.WindowModality.WindowModal)
        product_form_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        product_form_window.destroyed.connect(self._on_product_form_destroyed)
        product_form_window.accepted.connect(self._refresh_product_list)
        product_form_window.show()

    def _on_product_form_destroyed(self, *args):
        self.edit_open = False

    def _delete_product(self, product_id):
        if product_in_orders(product_id):
            QMessageBox.warning(self, "Ошибка", "Товар в заказе, удалить нельзя.")
            return
        delete_product(product_id)
        self._refresh_product_list()
