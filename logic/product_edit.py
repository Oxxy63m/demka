# product_edit.py
from App.db import (
    get_category_names,
    get_manufacturer_names,
    get_product_by_id,
    insert_product,
    update_product,
)


def load_product(pid):
    return get_product_by_id(pid)


def save_product(pid, data):
    if pid is None:
        insert_product(data)
    else:
        update_product(pid, data)


__all__ = [
    "get_category_names",
    "get_manufacturer_names",
    "get_product_by_id",
    "insert_product",
    "update_product",
    "load_product",
    "save_product",
]
