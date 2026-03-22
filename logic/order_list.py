from App.db import get_orders_all, delete_order as _del_order


def load_orders():
    return get_orders_all()


def delete_order(order_id):
    return _del_order(order_id)
