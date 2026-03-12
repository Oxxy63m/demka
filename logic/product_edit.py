# Форма товара: загрузка по id, сохранение, списки категорий и производителей.
import os

from App.db import (
    get_product_by_id as _get_product_by_id,
    get_category_names as _get_category_names,
    get_manufacturer_names as _get_manufacturer_names,
    insert_product as _insert_product,
    update_product as _update_product,
)
from App.config import DATA_DIR


def get_category_names():
    """Возвращает список категорий для выпадающего списка в форме товара."""
    return _get_category_names()


def get_manufacturer_names():
    """Возвращает список производителей для выпадающего списка в форме товара."""
    return _get_manufacturer_names()


def load_product(product_id):
    """Загружает один товар по id из БД. Возвращает словарь или None."""
    return _get_product_by_id(product_id)


def save_product(product_id, data, old_photo_path=None):
    """Сохраняет товар: при product_id=None — добавление, иначе обновление. data — словарь полей. old_photo_path — старый путь фото при редактировании (при смене фото файл удаляется)."""
    if old_photo_path and old_photo_path != data.get("photo"):
        old_full = os.path.join(DATA_DIR, old_photo_path)
        if os.path.isfile(old_full):
            try:
                os.remove(old_full)
            except OSError:
                pass
    if product_id is None:
        _insert_product(data)
    else:
        _update_product(product_id, data)
