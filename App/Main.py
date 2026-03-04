# Главное окно приложения: каталог товаров, фильтры, корзина, кнопки «Заказы» и «Добавить». Разметка — ui/main.ui.
from PySide6.QtWidgets import QMainWindow, QMessageBox, QSizePolicy, QDialog, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtUiTools import loadUiType

from App.config import UI, ROLE_MANAGER, ROLE_ADMINISTRATOR, ROLE_CLIENT, ROLE_GUEST
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
        self.cart = []  # корзина для клиента: список {product_id, product_name, price, quantity}
        self.setWindowTitle("Список товаров")
        self.lbl_title.setStyleSheet("font-weight: bold; font-size: 18pt;")
        self.lbl_user.setWordWrap(True)
        self.lbl_user.setText(user.get("full_name", "Гость"))
        search_and_filter_widgets = (self.lbl_search, self.search_edit, self.lbl_supplier, self.supplier_combo, self.lbl_sort, self.sort_combo)
        self.btn_orders.clicked.connect(self._open_orders)
        # Кнопка «Заказ» — видна гостю и клиенту, по нажатию открывается корзина
        btn_cart = getattr(self, "btn_cart", None) or self.findChild(QPushButton, "btn_cart")
        if btn_cart is not None:
            btn_cart.setVisible(self.role in (ROLE_CLIENT, ROLE_GUEST))
            btn_cart.clicked.connect(self._open_cart)
        if self.role not in (ROLE_MANAGER, ROLE_ADMINISTRATOR):
            self.btn_orders.setVisible(self.role != "guest")
            for widget in search_and_filter_widgets:
                widget.setVisible(False)
            self.btn_add.setVisible(False)
        else:
            self.search_edit.textChanged.connect(self._refresh_product_list)
            self.supplier_combo.addItem("Все поставщики", None)
            self.supplier_combo.currentIndexChanged.connect(self._refresh_product_list)
            self.sort_combo.addItem("—", None)
            self.sort_combo.addItem("По возрастанию кол-ва", "asc")
            self.sort_combo.addItem("По убыванию кол-ва", "desc")
            self.sort_combo.currentIndexChanged.connect(self._refresh_product_list)
            for supplier_name in get_supplier_names():
                self.supplier_combo.addItem(supplier_name, supplier_name)
        if self.role != ROLE_ADMINISTRATOR:
            self.btn_add.setVisible(False)
        else:
            self.btn_add.clicked.connect(self._on_add)
        self.btn_logout.clicked.connect(self.close)
        self.cards_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._refresh_product_list()

    def _refresh_product_list(self):
        """Загружает список товаров из БД по фильтрам и заполняет каталог карточками."""
        search_text = self.search_edit.text() if self.search_edit.isVisible() else ""
        supplier_filter = self.supplier_combo.currentData()
        sort_by_quantity = self.sort_combo.currentData()
        try:
            product_list = load_products(search_text, supplier_filter, sort_by_quantity)
        except Exception as load_error:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки данных: {load_error}")
            return
        while self.cards_layout.count():
            layout_item = self.cards_layout.takeAt(0)
            if layout_item.widget():
                layout_item.widget().deleteLater()
        user_is_administrator = self.role == ROLE_ADMINISTRATOR
        user_is_client = self.role == ROLE_CLIENT
        for product in product_list:
            card = Card(product, is_admin=user_is_administrator, is_client=user_is_client)
            if user_is_administrator:
                card.clicked.connect(self._open_product_edit_form)
                card.delete_requested.connect(self._on_delete_product_card)
            if user_is_client:
                card.add_to_cart.connect(self._add_to_cart)
            self.cards_layout.addWidget(card)

    def _open_orders(self):
        """Открывает окно со списком заказов."""
        from App.Orders import Orders
        # Ссылку храним в self, иначе окно уничтожается сборщиком мусора и сразу закрывается
        self._orders_window = Orders(self.user, parent=None)
        self._orders_window.setWindowTitle("Заказы")
        self._orders_window.showMaximized()

    def _open_cart(self):
        """Открывает диалог корзины; после подтверждения заказа корзина очищается."""
        from App.Cart import Cart
        cart_dialog = Cart(self.user, self.cart, self)
        if cart_dialog.exec() == QDialog.DialogCode.Accepted:
            self.cart.clear()

    def _add_to_cart(self, item):
        """Добавляет товар в корзину или увеличивает количество, если уже есть."""
        for it in self.cart:
            if it.get("product_id") == item.get("product_id"):
                it["quantity"] = it.get("quantity", 0) + item.get("quantity", 1)
                return
        self.cart.append({"product_id": item["product_id"], "product_name": item["product_name"], "price": item["price"], "quantity": item.get("quantity", 1)})

    def _open_product_edit_form(self, product_id):
        """Открывает форму добавления или редактирования товара (product_id=None — новый товар)."""
        if self.edit_open:
            QMessageBox.warning(self, "Предупреждение", "Закройте окно редактирования.")
            return
        from App.ProdForm import ProdForm
        self.edit_open = True
        product_form_window = ProdForm(product_id, self)
        product_form_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        product_form_window.destroyed.connect(lambda: setattr(self, "edit_open", False))
        product_form_window.accepted.connect(self._refresh_product_list)
        product_form_window.show()

    def _on_add(self):
        """Кнопка «Добавить»: открывает форму нового товара."""
        self._open_product_edit_form(None)

    def _on_delete_product_card(self, product_id):
        """Удаляет товар из БД после подтверждения; если товар в заказе — отказ."""
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
            self._refresh_product_list()
        except Exception as delete_error:
            QMessageBox.critical(self, "Ошибка", str(delete_error))
