# logic/order_list.py — логика списка заказов (используется order_list_window)
import os
import sys

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from App.db import get_orders_all as _get_orders_all, delete_order as _delete_order


def load_orders():
    """Список всех заказов с ФИО клиента."""
    return _get_orders_all()


def delete_order(order_id):
    """Удалить заказ."""
    _delete_order(order_id)
