# Логика формы заказа: загрузка по id, сохранение (добавление/редактирование), статусы и список пользователей.
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
    """Возвращает список статусов заказа для выпадающего списка в форме заказа."""
    return list(ORDER_STATUSES)


def get_users_list():
    """Возвращает список пользователей (user_id, full_name) для выбора клиента в заказе."""
    return _get_users_list()


def load_order(order_id):
    """Загружает один заказ по id из БД. Возвращает словарь или None."""
    return _get_order_by_id(order_id)


def save_order(order_id, data):
    """Сохраняет заказ: при order_id=None — добавление, иначе обновление. data — даты, пункт выдачи, статус, user_id."""
    if order_id is None:
        _insert_order(data)
    else:
        _update_order(order_id, data)
