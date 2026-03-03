# =============================================================================
# ИМПОРТ ДАННЫХ ИЗ EXCEL В БАЗУ
# Запуск: python import_to_db.py
# Что делает: читает xlsx из папки DATA_DIR (задаётся в App/config.py) и
# заполняет таблицы: пользователи, товары, заказы, пункты выдачи.
# Нужные файлы: user_import.xlsx, Tovar.xlsx, Заказ_import.xlsx и др.
# =============================================================================
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
    get_or_create_pickup_point_id_conn,
    get_or_create_status_id_conn,
)

# Папка с xlsx и фото — из App.config (та же, откуда приложение грузит картинки)

PATH_USERS = os.path.join(DATA_DIR, "user_import.xlsx")
PATH_PRODUCTS = os.path.join(DATA_DIR, "Tovar.xlsx")
PATH_ORDERS = os.path.join(DATA_DIR, "Заказ_import.xlsx")
PATH_POINTS = os.path.join(DATA_DIR, "Пункты выдачи_import.xlsx")
PATH_ORDER_ITEMS = os.path.join(DATA_DIR, "order_items.xlsx")

# Роль из Excel → значение в БД
ROLE = {"администратор": "administrator", "менеджер": "manager", "клиент": "client"}


def load_pickup_addresses(path_to_file):
    """
    Читает файл с адресами пунктов выдачи (первый столбец).
    Возвращает список: индекс 0 = адрес для номера 1 в Excel, индекс 1 = для номера 2 и т.д.
    """
    if not os.path.isfile(path_to_file):
        return []
    points_dataframe = pd.read_excel(path_to_file, header=None)
    addresses = []
    for row_index in range(len(points_dataframe)):
        address = str(points_dataframe.iloc[row_index, 0]).strip()
        if address:
            addresses.append(address)
    print(f"✅ Загружено пунктов выдачи: {len(addresses)}")
    return addresses


def import_users(connection, path_to_file):
    """Импортирует пользователей в БД (3НФ: role_id)."""
    users_dataframe = pd.read_excel(path_to_file)
    cursor = connection.cursor()
    for _, user_row in users_dataframe.iterrows():
        login = str(user_row.get("Логин", "") or "").strip()
        if not login:
            continue
        role_russian = str(user_row.get("Роль сотрудника", "клиент") or "клиент").strip().lower()
        role_name = ROLE.get(role_russian, role_russian)
        role_id = get_or_create_role_id(connection, role_name)
        if role_id is None:
            continue
        cursor.execute(
            """
            INSERT INTO users (full_name, login, user_password, role_id)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (login) DO NOTHING;
            """,
            (str(user_row.get("ФИО", "") or ""), login, str(user_row.get("Пароль", "") or ""), role_id),
        )
    cursor.close()
    print(f"✅ Импортировано пользователей: {len(users_dataframe)}")
    return len(users_dataframe)


def import_products(connection, path_to_file):
    """Импортирует товары в БД (3НФ: supplier_id, manufacturer_id, category_id)."""
    products_dataframe = pd.read_excel(path_to_file)
    cursor = connection.cursor()
    for _, product_row in products_dataframe.iterrows():
        product_name = product_row.get("Наименование товара")
        if pd.isna(product_name) or not str(product_name).strip():
            continue
        photo_filename = product_row.get("Фото")
        if pd.isna(photo_filename) or not str(photo_filename).strip():
            photo_filename = "picture.png"
        else:
            photo_filename = str(photo_filename).strip()
        price = product_row.get("Цена")
        price = float(price) if price is not None and not pd.isna(price) else 0
        discount = product_row.get("Действующая скидка")
        discount = float(discount) if discount is not None and not pd.isna(discount) else 0
        stock_quantity = product_row.get("Кол-во на складе")
        stock_quantity = int(float(stock_quantity)) if stock_quantity is not None and not pd.isna(stock_quantity) else 0
        supplier_id = get_or_create_supplier_id_conn(connection, product_row.get("Поставщик"))
        manufacturer_id = get_or_create_manufacturer_id_conn(connection, product_row.get("Производитель"))
        category_id = get_or_create_category_id_conn(connection, product_row.get("Категория товара"))
        cursor.execute(
            """
            INSERT INTO products (
                article, product_name, unit, price, supplier_id, manufacturer_id,
                category_id, discount, stock_quantity, description, photo
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """,
            (
                product_row.get("Артикул"),
                str(product_name).strip(),
                product_row.get("Единица измерения") or "шт.",
                price,
                supplier_id,
                manufacturer_id,
                category_id,
                discount,
                stock_quantity,
                product_row.get("Описание товара"),
                photo_filename,
            ),
        )
    cursor.close()
    print(f"✅ Импортировано товаров: {len(products_dataframe)}")
    return len(products_dataframe)


def import_orders(connection, path_to_file, pickup_addresses):
    """
    Импортирует заказы в БД (3НФ: pickup_point_id, status_id).
    pickup_addresses — список адресов (индекс 0 = номер 1 в Excel).
    """
    orders_dataframe = pd.read_excel(path_to_file)
    cursor = connection.cursor()
    cursor.execute("SELECT user_id, full_name FROM users")
    user_id_by_full_name = {
        str(full_name).strip().lower(): user_id
        for user_id, full_name in cursor.fetchall()
        if full_name
    }
    imported_orders_count = 0

    for _, order_row in orders_dataframe.iterrows():
        order_date = pd.to_datetime(order_row["Дата заказа"], errors="coerce")
        if pd.isna(order_date):
            print(f"⏩ Пропуск заказа: неверная дата ({order_row['Дата заказа']})")
            continue
        order_date = order_date.date()

        delivery_date = pd.to_datetime(order_row["Дата доставки"], errors="coerce")
        delivery_date = delivery_date.date() if not pd.isna(delivery_date) else None

        client_full_name = str(order_row["ФИО авторизированного клиента"]).strip()
        user_id = user_id_by_full_name.get(client_full_name.lower()) if client_full_name else None
        if user_id is None and pd.notna(order_row.get("Номер клиента")):
            try:
                user_id = int(float(order_row["Номер клиента"]))
            except (TypeError, ValueError):
                pass
        if user_id is None:
            print(f"⏩ Пропуск заказа: клиент не найден ({client_full_name})")
            continue

        pickup_point_value = order_row["Адрес пункта выдачи"]
        pickup_address_string = None
        if pickup_addresses and pickup_point_value is not None and not pd.isna(pickup_point_value):
            try:
                pickup_index = int(float(pickup_point_value))
                if 1 <= pickup_index <= len(pickup_addresses):
                    pickup_address_string = pickup_addresses[pickup_index - 1]
            except (TypeError, ValueError):
                pickup_address_string = str(pickup_point_value).strip() if str(pickup_point_value).strip() else None
        elif pickup_point_value is not None and not pd.isna(pickup_point_value):
            pickup_address_string = str(pickup_point_value).strip()

        pickup_code = None
        if pd.notna(order_row.get("Код для получения")):
            try:
                pickup_code = int(float(order_row["Код для получения"]))
            except (TypeError, ValueError):
                pass
        status = str(order_row.get("Статус заказа", "") or "").strip() or None

        # Артикул заказа из Excel (колонка "Артикул заказа" или "Артикул")
        order_article = order_row.get("Артикул заказа") or order_row.get("Артикул")
        if order_article is not None and not pd.isna(order_article):
            order_article = str(order_article).strip()
        else:
            order_article = None

        pickup_point_id = get_or_create_pickup_point_id_conn(connection, pickup_address_string) if pickup_address_string else None
        status_id = get_or_create_status_id_conn(connection, status)

        cursor.execute(
            """
            INSERT INTO orders (order_article, order_date, delivery_date, pickup_point_id, user_id, pickup_code, status_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
            """,
            (order_article, order_date, delivery_date, pickup_point_id, user_id, pickup_code, status_id),
        )
        imported_orders_count += 1
    cursor.close()
    print(f"✅ Импортировано заказов: {imported_orders_count}")
    return imported_orders_count


def import_order_items(database_cursor, path_to_file):
    """Импортирует позиции заказов в order_items (если есть файл order_items.xlsx)."""
    if not os.path.isfile(path_to_file):
        return 0
    order_items_dataframe = pd.read_excel(path_to_file)
    for _, item_row in order_items_dataframe.iterrows():
        order_id_raw = item_row.get("Номер заказа")
        product_id_raw = item_row.get("Номер товара")
        if order_id_raw is None or product_id_raw is None or pd.isna(order_id_raw) or pd.isna(product_id_raw):
            continue
        try:
            order_id = int(float(order_id_raw))
            product_id = int(float(product_id_raw))
        except (TypeError, ValueError):
            continue
        quantity = item_row.get("Количество", 1)
        quantity = int(float(quantity)) if quantity is not None and not pd.isna(quantity) else 1
        database_cursor.execute(
            "INSERT INTO order_items (order_id, product_id, quantity) VALUES (%s, %s, %s)",
            (order_id, product_id, quantity),
        )
    print(f"✅ Импортировано позиций заказов: {len(order_items_dataframe)}")
    return len(order_items_dataframe)


def main():
    """Основная функция импорта данных."""
    database_connection = psycopg2.connect(**DB_CONFIG)
    database_cursor = database_connection.cursor()

    try:
        print("🚀 Начинаем импорт данных...\n")

        pickup_addresses = load_pickup_addresses(PATH_POINTS)
        import_users(database_connection, PATH_USERS)
        import_products(database_connection, PATH_PRODUCTS)
        import_orders(database_connection, PATH_ORDERS, pickup_addresses)
        import_order_items(database_cursor, PATH_ORDER_ITEMS)

        database_connection.commit()
        print(f"\n{'='*50}")
        print("🎉 Импорт завершён успешно!")
        print(f"{'='*50}")

    except Exception as import_error:
        database_connection.rollback()
        print(f"\n❌ Ошибка при импорте: {import_error}")
        import traceback
        traceback.print_exc()
    finally:
        database_cursor.close()
        database_connection.close()


if __name__ == "__main__":
    main()
