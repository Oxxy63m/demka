# App/Main.py — главное окно (каталог товаров), разметка из UI/main.ui
from PySide6.QtWidgets import QMainWindow, QMessageBox, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtUiTools import loadUiType

from App.config import UI, ROLE_MANAGER, ROLE_ADMINISTRATOR
from App.Card import Card
from logic.product_list import load_products, get_supplier_names, product_in_orders, delete_product

Ui_Main, BaseMain = loadUiType(UI["main"])


class Main(BaseMain, Ui_Main):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.user = user
        self.role = user.get("role", "guest")
        self.edit_open = False
        self.setWindowTitle("Список товаров")
        self.lbl_title.setStyleSheet("font-weight: bold; font-size: 18pt;")
        self.lbl_user.setWordWrap(True)
        self.lbl_user.setText(user.get("full_name", "Гость"))
        _filter_widgets = (self.lbl_search, self.search_edit, self.lbl_supplier, self.supplier_combo, self.lbl_sort, self.sort_combo)
        if self.role not in (ROLE_MANAGER, ROLE_ADMINISTRATOR):
            self.btn_orders.setVisible(False)
            for w in _filter_widgets:
                w.setVisible(False)
            self.btn_add.setVisible(False)
        else:
            self.btn_orders.clicked.connect(self._open_orders)
            self.search_edit.textChanged.connect(self._refresh_list)
            self.supplier_combo.addItem("Все поставщики", None)
            self.supplier_combo.currentIndexChanged.connect(self._refresh_list)
            self.sort_combo.addItem("—", None)
            self.sort_combo.addItem("По возрастанию кол-ва", "asc")
            self.sort_combo.addItem("По убыванию кол-ва", "desc")
            self.sort_combo.currentIndexChanged.connect(self._refresh_list)
            for s in get_supplier_names():
                self.supplier_combo.addItem(s, s)
        if self.role != ROLE_ADMINISTRATOR:
            self.btn_add.setVisible(False)
        else:
            self.btn_add.clicked.connect(self._on_add)
        self.btn_logout.clicked.connect(self.close)
        self.cards_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._refresh_list()

    def _refresh_list(self):
        search = self.search_edit.text() if self.search_edit.isVisible() else ""
        supplier = self.supplier_combo.currentData()
        order_by = self.sort_combo.currentData()
        try:
            rows = load_products(search, supplier, order_by)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки данных: {e}")
            return
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        is_admin = self.role == ROLE_ADMINISTRATOR
        for product in rows:
            card = Card(product, is_admin=is_admin)
            if is_admin:
                card.clicked.connect(self._open_edit)
                card.delete_requested.connect(self._on_delete_card)
            self.cards_layout.addWidget(card)

    def _open_orders(self):
        from App.Orders import Orders
        win = Orders(self.user, parent=None)
        win.setWindowTitle("Заказы")
        win.showMaximized()

    def _open_edit(self, product_id):
        if self.edit_open:
            QMessageBox.warning(self, "Предупреждение", "Закройте окно редактирования.")
            return
        from App.ProdForm import ProdForm
        self.edit_open = True
        w = ProdForm(product_id, self)
        w.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        w.destroyed.connect(lambda: setattr(self, "edit_open", False))
        w.accepted.connect(self._refresh_list)
        w.show()

    def _on_add(self):
        self._open_edit(None)

    def _on_delete_card(self, product_id):
        if product_in_orders(product_id):
            QMessageBox.warning(self, "Ошибка", "Товар в заказе, удалить нельзя.")
            return
        if QMessageBox.question(
            self, "Подтверждение", "Удалить товар?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return
        try:
            delete_product(product_id)
            QMessageBox.information(self, "Готово", "Товар удалён.")
            self._refresh_list()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
