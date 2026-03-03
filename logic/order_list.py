# Список заказов для окна «Заказы»
import os, sys
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)
from App.db import get_orders_all, delete_order as _del_order

def load_orders():
    return get_orders_all()

def delete_order(order_id):
    return _del_order(order_id)
