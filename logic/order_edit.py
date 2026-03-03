# Форма заказа: загрузка по id, сохранение (добавление/редактирование), статусы и список пользователей.
import os
import sys

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from App.config import ORDER_STATUSES
from App.db import (
    get_order_by_id as _get_order_by_id,
    get_users_list as _get_users_list,
    insert_order as _insert_order,
    update_order as _update_order,
)


def get_order_statuses():
    """Список статусов заказа для выпадающего списка."""
    return list(ORDER_STATUSES)


def get_users_list():
    """Список пользователей для выбора в заказе."""
    return _get_users_list()


def load_order(order_id):
    """Загрузить заказ по id. Возвращает словарь или None."""
    return _get_order_by_id(order_id)


def save_order(order_id, data):
    """Сохранить заказ. order_id=None — добавление, иначе обновление."""
    if order_id is None:
        _insert_order(data)
    else:
        _update_order(order_id, data)
