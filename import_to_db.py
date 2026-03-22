# Импорт из Excel в БД. Запуск: python import_to_db.py. Файлы в папке DATA_DIR (App/config.py).
import os
import sys

import pandas as pd
import psycopg2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from App.config import DB_CONFIG, DATA_DIR
from App.db import (
    get_or_create_role_id,
    get_or_create_supplier_id_conn,
    get_or_create_manufacturer_id_conn,
    get_or_create_category_id_conn,
    get_or_create_unit_id_conn,
    get_or_create_pickup_point_id_conn,
    get_or_create_status_id_conn,
)

PATHS = {
    "users": os.path.join(DATA_DIR, "user_import.xlsx"),
    "products": os.path.join(DATA_DIR, "Tovar.xlsx"),
    "orders": os.path.join(DATA_DIR, "Заказ_import.xlsx"),
    "points": os.path.join(DATA_DIR, "Пункты выдачи_import.xlsx"),
    "order_items": os.path.join(DATA_DIR, "order_items.xlsx"),
}
ROLE = {"администратор": "administrator", "менеджер": "manager", "клиент": "client"}


def _num(x, default=0, kind=float):
    if x is None:
        return default
    if isinstance(x, float) and pd.isna(x):
        return default
    return kind(float(x))


def _str(x, default=""):
    if x is None:
        return default
    s = str(x).strip()
    if not s:
        return default
    if s.lower() in ("nan", "nat", "none"):
        return default
    return s


def load_pickup_addresses(path):
    if not os.path.isfile(path):
        return []
    df = pd.read_excel(path, header=None)
    result = []
    for i in range(len(df)):
        value = _str(df.iloc[i, 0])
        if value:
            result.append(value)
    return result


def import_users(connection, path):
    df = pd.read_excel(path)
    cursor = connection.cursor()
    for _, row in df.iterrows():
        login = _str(row.get("Логин"))
        if not login:
            continue
        role_raw = _str(row.get("Роль сотрудника", "клиент"))
        role_name = ROLE.get(role_raw.lower(), role_raw)
        role_id = get_or_create_role_id(connection, role_name)
        if not role_id:
            continue
        cursor.execute(
            "INSERT INTO users (full_name, login, user_password, role_id) VALUES (%s, %s, %s, %s) ON CONFLICT (login) DO NOTHING",
            (_str(row.get("ФИО")), login, _str(row.get("Пароль")), role_id),
        )
    cursor.close()
    return len(df)


def import_products(connection, path):
    df = pd.read_excel(path)
    cursor = connection.cursor()
    for _, row in df.iterrows():
        product_name = _str(row.get("Наименование товара"))
        if not product_name:
            continue
        photo = _str(row.get("Фото")) or "picture.png"
        price = _num(row.get("Цена"))
        discount = _num(row.get("Действующая скидка"))
        stock_quantity = _num(row.get("Кол-во на складе"), 0, int)
        supplier_id = get_or_create_supplier_id_conn(connection, row.get("Поставщик"))
        manufacturer_id = get_or_create_manufacturer_id_conn(connection, row.get("Производитель"))
        category_id = get_or_create_category_id_conn(connection, row.get("Категория товара"))
        unit_id = get_or_create_unit_id_conn(connection, row.get("Единица измерения") or "шт.")
        cursor.execute(
            "INSERT INTO products (article, product_name, unit_id, price, supplier_id, manufacturer_id, category_id, discount, stock_quantity, description, photo) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                row.get("Артикул"),
                product_name,
                unit_id,
                price,
                supplier_id,
                manufacturer_id,
                category_id,
                discount,
                stock_quantity,
                row.get("Описание товара"),
                photo,
            ),
        )
    cursor.close()
    return len(df)


def import_orders(connection, path, pickup_addresses):
    df = pd.read_excel(path)
    cursor = connection.cursor()
    cursor.execute("SELECT user_id, full_name FROM users")
    user_by_name = {}
    rows = cursor.fetchall()
    for user_id, full_name in rows:
        if not full_name:
            continue
        key = _str(full_name).lower()
        user_by_name[key] = user_id
    count = 0
    for _, row in df.iterrows():
        order_date = pd.to_datetime(row.get("Дата заказа"), errors="coerce")
        if pd.isna(order_date):
            continue
        order_date = order_date.date()
        delivery_date = pd.to_datetime(row.get("Дата доставки"), errors="coerce")
        delivery_date = delivery_date.date() if not pd.isna(delivery_date) else None
        client_name = _str(row.get("ФИО авторизированного клиента"))
        user_id = user_by_name.get(client_name.lower())
        if user_id is None and pd.notna(row.get("Номер клиента")):
            user_id = int(float(row["Номер клиента"]))
        if user_id is None:
            continue
        pp_val = row.get("Адрес пункта выдачи")
        pickup_addr = _str(pp_val) if pp_val is not None and not pd.isna(pp_val) else None
        if pickup_addr and pickup_addresses:
            idx = int(float(pp_val))
            if 1 <= idx <= len(pickup_addresses):
                pickup_addr = pickup_addresses[idx - 1]
        pickup_code = _num(row.get("Код для получения"), None, int)
        status_id = get_or_create_status_id_conn(connection, _str(row.get("Статус заказа")))
        pickup_point_id = get_or_create_pickup_point_id_conn(connection, pickup_addr) if pickup_addr else None
        cursor.execute(
            "INSERT INTO orders (order_date, delivery_date, pickup_point_id, user_id, pickup_code, status_id) VALUES (%s, %s, %s, %s, %s, %s)",
            (order_date, delivery_date, pickup_point_id, user_id, pickup_code, status_id),
        )
        count += 1
    cursor.close()
    return count


def import_order_items(cursor, path):
    if not os.path.isfile(path):
        return 0
    df = pd.read_excel(path)
    for _, row in df.iterrows():
        order_id_val = row.get("Номер заказа")
        product_id_val = row.get("Номер товара")
        if order_id_val is None or product_id_val is None or pd.isna(order_id_val) or pd.isna(product_id_val):
            continue
        order_id_val = int(float(order_id_val))
        product_id_val = int(float(product_id_val))
        quantity = _num(row.get("Количество", 1), 1, int)

        # В актуальной схеме нет unit_price в order_items
        cursor.execute(
            "INSERT INTO order_items (order_id, product_id, quantity) VALUES (%s, %s, %s)",
            (order_id_val, product_id_val, quantity),
        )
    return len(df)


def main():
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()
    cursor.execute(
        "TRUNCATE "
        "order_items, orders, products, users, roles, suppliers, manufacturers, categories, "
        "units, statuses, pickup_points "
        "RESTART IDENTITY CASCADE"
    )

    pickup_addresses = load_pickup_addresses(PATHS["points"])
    import_users(connection, PATHS["users"])
    import_products(connection, PATHS["products"])
    import_orders(connection, PATHS["orders"], pickup_addresses)
    import_order_items(cursor, PATHS["order_items"])
    connection.commit()
    cursor.close()
    connection.close()


if __name__ == "__main__":
    main()

