# Импорт из Excel в БД. Запуск: python load_xlsx.py
import os
import sys

import pandas as pd
import psycopg2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DB_CONFIG

# Откуда брать xlsx (папка import рядом со скриптом)
IMPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "import")

PATH_USERS = os.path.join(IMPORT_DIR, "user_import.xlsx")
PATH_PRODUCTS = os.path.join(IMPORT_DIR, "Tovar.xlsx")
PATH_ORDERS = os.path.join(IMPORT_DIR, "Заказ_import.xlsx")
PATH_POINTS = os.path.join(IMPORT_DIR, "Пункты выдачи_import.xlsx")
PATH_ORDER_ITEMS = os.path.join(IMPORT_DIR, "order_items.xlsx")

# Как в xlsx написана роль → как пишем в БД
ROLE_MAP = {"администратор": "administrator", "менеджер": "manager", "авторизированный клиент": "client", "клиент": "client"}


def get_cell_value(row, *column_names):
    """Достаём из строки значение по названию столбца (подставляем первое из списка, что найдётся)."""
    for name in column_names:
        if name in row and pd.notna(row.get(name)) and str(row.get(name)).strip() != "":
            return row[name]
    return None


def import_users(cursor, path):
    """Читаем xlsx с пользователями и пишем в таблицу users."""
    users_df = pd.read_excel(path)
    for _, row in users_df.iterrows():
        role_raw = get_cell_value(row, "Роль сотрудника", "роль", "role") or "client"
        role_normalized = ROLE_MAP.get(str(role_raw).strip().lower(), str(role_raw).strip())
        full_name = str(get_cell_value(row, "ФИО", "full_name") or "").strip()
        login = str(get_cell_value(row, "Логин", "login") or "").strip()
        password = str(get_cell_value(row, "Пароль", "user_password") or "").strip()
        if not login:
            continue
        cursor.execute(
            "INSERT INTO users (full_name, login, user_password, role) VALUES (%s, %s, %s, %s)",
            (full_name, login, password, role_normalized),
        )
    print(f"Пользователей: {len(users_df)}")


def import_products(cursor, path):
    """Читаем xlsx с товарами и пишем в таблицу products."""
    products_df = pd.read_excel(path)
    for _, row in products_df.iterrows():
        product_name = get_cell_value(row, "Наименование товара", "наименование", "product_name")
        if not product_name:
            continue
        price = get_cell_value(row, "Цена", "price")
        price = float(price) if price is not None else 0
        discount = get_cell_value(row, "Действующая скидка", "скидка", "discount")
        discount = float(discount) if discount is not None else 0
        stock_quantity = get_cell_value(row, "Кол-во на складе", "количество", "stock_quantity")
        stock_quantity = int(float(stock_quantity)) if stock_quantity is not None else 0
        photo = get_cell_value(row, "Фото", "photo")
        photo = str(photo).strip() if photo else "picture.png"

        article = str(get_cell_value(row, "Артикул", "article") or "").strip()
        unit = str(get_cell_value(row, "Единица измерения", "ед.изм", "unit") or "шт.").strip()
        supplier = str(get_cell_value(row, "Поставщик", "supplier") or "").strip() or None
        manufacturer = str(get_cell_value(row, "Производитель", "manufacturer") or "").strip() or None
        category = str(get_cell_value(row, "Категория товара", "категория", "category") or "").strip() or None
        description = str(get_cell_value(row, "Описание товара", "описание", "description") or "").strip() or None

        cursor.execute(
            "INSERT INTO products (article, product_name, unit, price, supplier, manufacturer, category, discount, stock_quantity, description, photo) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (article, str(product_name).strip(), unit, price, supplier, manufacturer, category, discount, stock_quantity, description, photo),
        )
    print(f"Товаров: {len(products_df)}")


def import_orders(cursor, path, pickup_addresses=None):
    """Читаем xlsx с заказами и пишем в orders. Если передан список адресов — в ячейке может быть номер (1, 2…), подставим адрес."""
    orders_df = pd.read_excel(path)
    cursor.execute("SELECT user_id, full_name FROM users")
    user_id_by_full_name = {str(full_name).strip().lower(): user_id for user_id, full_name in cursor.fetchall() if full_name}

    for row_index, row in orders_df.iterrows():
        order_date_raw = get_cell_value(row, "Дата заказа", "order_date")
        order_date = pd.to_datetime(order_date_raw, errors="coerce")
        if pd.isna(order_date):
            print(f"Строка {row_index + 2}: плохая дата заказа — пропускаем")
            continue
        order_date = order_date.date()

        delivery_date_raw = get_cell_value(row, "Дата доставки", "delivery_date")
        delivery_date = pd.to_datetime(delivery_date_raw, errors="coerce")
        delivery_date = delivery_date.date() if not pd.isna(delivery_date) else None

        client_full_name = str(get_cell_value(row, "ФИО авторизированного клиента", "user_full_name") or "").strip()
        user_id = user_id_by_full_name.get(client_full_name.lower())
        if user_id is None:
            user_id_raw = get_cell_value(row, "Номер клиента", "user_id")
            user_id = int(user_id_raw) if user_id_raw is not None and pd.notna(user_id_raw) else None
        if user_id is None:
            print(f"Строка {row_index + 2}: нет такого клиента ({client_full_name}) — пропускаем")
            continue

        pickup_point_value = get_cell_value(row, "Адрес пункта выдачи", "адрес", "pickup_point")
        if pickup_addresses and pickup_point_value is not None:
            try:
                pickup_index = int(float(pickup_point_value))
                if 1 <= pickup_index <= len(pickup_addresses):
                    pickup_point_value = pickup_addresses[pickup_index - 1]
            except (TypeError, ValueError):
                pass
        pickup_point_str = None
        if pickup_point_value is not None and not (isinstance(pickup_point_value, float) and pd.isna(pickup_point_value)):
            pickup_point_str = str(pickup_point_value).strip()

        pickup_code_raw = get_cell_value(row, "Код для получения", "код", "pickup_code")
        pickup_code = int(float(pickup_code_raw)) if pickup_code_raw is not None and pd.notna(pickup_code_raw) else None
        order_status = str(get_cell_value(row, "Статус заказа", "статус", "status") or "").strip() or None

        cursor.execute(
            "INSERT INTO orders (order_date, delivery_date, pickup_point, user_id, pickup_code, status) VALUES (%s, %s, %s, %s, %s, %s)",
            (order_date, delivery_date, pickup_point_str, user_id, pickup_code, order_status),
        )
    print(f"Заказов: {len(orders_df)}")


def import_order_items(cursor, path):
    """Читаем xlsx с позициями заказов (какой заказ, какой товар, сколько) и пишем в order_items."""
    order_items_df = pd.read_excel(path)
    for _, row in order_items_df.iterrows():
        order_id_raw = get_cell_value(row, "Номер заказа", "order_id")
        product_id_raw = get_cell_value(row, "Номер товара", "product_id")
        quantity_raw = get_cell_value(row, "Количество", "кол-во", "quantity")
        if order_id_raw is None or product_id_raw is None:
            continue
        order_id = int(float(order_id_raw))
        product_id = int(float(product_id_raw))
        quantity = int(float(quantity_raw)) if quantity_raw is not None else 1
        cursor.execute("INSERT INTO order_items (order_id, product_id, quantity) VALUES (%s, %s, %s)", (order_id, product_id, quantity))
    print(f"Позиций заказов: {len(order_items_df)}")


def main():
    # Сначала читаем адреса пунктов выдачи: в заказах в xlsx может стоять цифра 1, 2… — подставим сюда адрес
    pickup_addresses = None
    if os.path.isfile(PATH_POINTS):
        points_df = pd.read_excel(PATH_POINTS, header=None)
        pickup_addresses = [str(points_df.iloc[i, 0]).strip() for i in range(len(points_df)) if pd.notna(points_df.iloc[i, 0]) and str(points_df.iloc[i, 0]).strip()]

    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()
    try:
        print("Импорт...")
        import_users(cursor, PATH_USERS)
        import_products(cursor, PATH_PRODUCTS)
        import_orders(cursor, PATH_ORDERS, pickup_addresses)
        if os.path.isfile(PATH_ORDER_ITEMS):
            import_order_items(cursor, PATH_ORDER_ITEMS)
        connection.commit()
        print("Готово.")
    except Exception as e:
        connection.rollback()
        print(f"Ошибка: {e}")
        raise
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()
