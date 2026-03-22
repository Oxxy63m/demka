# order_list.py
from App.db import delete_order, get_orders_all

load_orders = get_orders_all
__all__ = ["load_orders", "delete_order", "get_orders_all"]
