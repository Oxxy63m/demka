# Форма товара: загрузка по id, сохранение. Категории и производители из БД.
from App.db import (
    get_product_by_id as _get_product_by_id,
    get_category_names as _get_category_names,
    get_manufacturer_names as _get_manufacturer_names,
    insert_product as _insert_product,
    update_product as _update_product,
)


def get_category_names():
    return _get_category_names()


def get_manufacturer_names():
    return _get_manufacturer_names()


def load_product(product_id):
    return _get_product_by_id(product_id)


def save_product(product_id, data, old_photo_path=None):
    import os
    if old_photo_path and old_photo_path != data.get("photo"):
        old_full = os.path.join("resources", old_photo_path)
        if os.path.isfile(old_full):
            try:
                os.remove(old_full)
            except OSError:
                pass
    if product_id is None:
        _insert_product(data)
    else:
        _update_product(product_id, data)
