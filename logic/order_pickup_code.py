"""
Строка «код заказа» (pickup_code): артикул, количество, артикул, количество, ...
Разделитель — запятая. В артикуле не должно быть запятой.
"""


def parse_order_pickup_code(text: str) -> list[tuple[str, int]]:
    """
    Разбирает строку на пары (артикул, количество).
    Пустая строка → пустой список (заказ без позиций в order_items).
    """
    s = (text or "").strip()
    if not s:
        return []

    parts = [p.strip() for p in s.split(",")]
    if len(parts) % 2 != 0:
        raise ValueError(
            "Неверный формат: нужно чётное число значений — пары «артикул, количество». "
            "Пример: ART-1, 2, ART-5, 1"
        )

    pairs: list[tuple[str, int]] = []
    for i in range(0, len(parts), 2):
        article = parts[i]
        qty_raw = parts[i + 1]
        if not article:
            raise ValueError("Встречен пустой артикул — проверьте лишние запятые.")
        if not qty_raw:
            raise ValueError(f"Не указано количество для артикула «{article}».")
        try:
            qty = int(qty_raw)
        except ValueError:
            raise ValueError(
                f"Количество для «{article}» должно быть целым числом (сейчас: «{qty_raw}»)."
            )
        if qty <= 0:
            raise ValueError(f"Количество для «{article}» должно быть больше нуля.")
        pairs.append((article, qty))

    return pairs
