# Список заказов: загрузка и удаление.
from App.db import get_orders_all, delete_order as _del_order


def load_orders():
    """Возвращает список всех заказов из БД (словари с id, датой, статусом, клиентом и т.д.)."""
    return get_orders_all()


def delete_order(order_id):
    """Удаляет заказ по id в БД."""
    return _del_order(order_id)
