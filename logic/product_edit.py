# logic/product_edit.py — логика формы товара: загрузка по id, сохранение (добавление/обновление), удаление старого фото (используется product_edit_window)
import os
import sys

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from App.db import (
    get_product_by_id as _get_product_by_id,
    get_category_names as _get_category_names,
    get_manufacturer_names as _get_manufacturer_names,
    insert_product as _insert_product,
    update_product as _update_product,
)
from App.utils import ROOT


def get_category_names():
    """Список категорий для выпадающего списка."""
    return _get_category_names()


def get_manufacturer_names():
    """Список производителей для выпадающего списка."""
    return _get_manufacturer_names()


def load_product(product_id):
    """Загрузить товар по id. Возвращает словарь или None."""
    return _get_product_by_id(product_id)


def save_product(product_id, data, old_photo_path=None):
    """
    Сохранить товар. product_id=None — добавление, иначе обновление.
    data — словарь полей (article, product_name, category, ... photo).
    old_photo_path — при обновлении старый путь фото; если он задан и заменён новым, файл удаляется.
    """
    if old_photo_path and old_photo_path != data.get("photo"):
        old_full = os.path.join(ROOT, old_photo_path)
        if os.path.isfile(old_full):
            try:
                os.remove(old_full)
            except OSError:
                pass
    if product_id is None:
        _insert_product(data)
    else:
        _update_product(product_id, data)
