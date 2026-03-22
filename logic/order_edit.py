# order_edit.py
from App.db import get_order_by_id, get_order_statuses, get_pickup_points, save_order

load_order = get_order_by_id
__all__ = ["get_order_by_id", "get_order_statuses", "get_pickup_points", "save_order", "load_order"]
