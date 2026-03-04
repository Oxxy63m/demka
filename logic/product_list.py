# Логика каталога товаров: загрузка списка, фильтры, проверка «товар в заказе», удаление.
import os
import sys

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)
from App.db import (
    get_products_all as _get_all,
    get_supplier_names as _get_supp,
    product_in_orders as _in_ord,
    delete_product as _del_prod,
)


def load_products(search_text="", supplier_name=None, order_by_quantity=None):
    """Возвращает список товаров с учётом поиска, фильтра по поставщику и сортировки по количеству."""
    return _get_all(search_text, supplier_name, order_by_quantity)


def get_supplier_names():
    """Список названий поставщиков для выпадающего списка фильтра."""
    return _get_supp()


def product_in_orders(product_id):
    """Проверяет, участвует ли товар хотя бы в одном заказе (нужно для запрета удаления)."""
    return _in_ord(product_id)


def delete_product(product_id):
    """Удаляет товар по id в БД."""
    return _del_prod(product_id)
