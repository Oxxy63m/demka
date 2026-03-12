# Форма заказа: загрузка по id, сохранение; статусы и пользователи — из БД.
from App.db import (
    get_order_by_id as _get_order_by_id,
    get_order_statuses as _get_order_statuses,
    get_users_list as _get_users_list,
    insert_order as _insert_order,
    update_order as _update_order,
)


def get_order_statuses():
    """Список статусов заказа для выпадающего списка (из БД)."""
    return _get_order_statuses()


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
