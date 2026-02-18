# logic/product_list.py — логика списка товаров: загрузка, поставщики, проверка в заказах, удаление (используется product_list_window)
import os
import sys

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from App.db import (
    get_products_all as _get_products_all,
    get_supplier_names as _get_supplier_names,
    product_in_orders as _product_in_orders,
    delete_product as _delete_product,
)


def load_products(search_text="", supplier_name=None, order_by_quantity=None):
    """Список товаров с поиском, фильтром по поставщику и сортировкой."""
    return _get_products_all(search_text, supplier_name, order_by_quantity)


def get_supplier_names():
    """Список поставщиков для фильтра."""
    return _get_supplier_names()


def product_in_orders(product_id):
    """Есть ли товар в заказах (удалять нельзя)."""
    return _product_in_orders(product_id)


def delete_product(product_id):
    """Удалить товар из БД."""
    _delete_product(product_id)
