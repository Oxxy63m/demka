from App.db import (
    get_order_by_id as _get_order_by_id,
    get_order_statuses as _get_order_statuses,
    get_users_list as _get_users_list,
    get_product_id_by_article as _get_product_id_by_article,
    save_order_with_items as _save_order_with_items,
)

from logic.order_pickup_code import parse_order_pickup_code


def get_order_statuses():
    return _get_order_statuses()


def get_users_list():
    return _get_users_list()


def load_order(order_id):
    return _get_order_by_id(order_id)


def _pickup_code_to_line_items(pickup_code: str) -> list[dict]:
    """Пары артикул–количество → список для order_items; один артикул дважды — суммируется."""
    pairs = parse_order_pickup_code(pickup_code)
    merged: dict[int, int] = {}
    for article, qty in pairs:
        pid = _get_product_id_by_article(article)
        if pid is None:
            raise ValueError(f'Товар с артикулом «{article}» не найден в каталоге.')
        merged[pid] = merged.get(pid, 0) + qty
    return [{"product_id": pid, "quantity": q} for pid, q in merged.items()]


def save_order(order_id, data):
    items = _pickup_code_to_line_items(data.get("pickup_code") or "")
    _save_order_with_items(order_id, data, items)
