# Импорт из Excel в БД. Запуск: python import_to_db.py
# Абсолютный путь к папке с xlsx задаётся в этом файле (DATA_DIR).
import os
import sys

import pandas as pd
import psycopg2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from App.config import DB_CONFIG

# Абсолютный путь к папке с файлами импорта (xlsx)
DATA_DIR = r"C:\Users\user\Documents\fuckdemoexam\Модуль 1"

PATH_USERS = os.path.join(DATA_DIR, "user_import.xlsx")
PATH_PRODUCTS = os.path.join(DATA_DIR, "Tovar.xlsx")
PATH_ORDERS = os.path.join(DATA_DIR, "Заказ_import.xlsx")
PATH_POINTS = os.path.join(DATA_DIR, "Пункты выдачи_import.xlsx")
PATH_ORDER_ITEMS = os.path.join(DATA_DIR, "order_items.xlsx")

# Роль из Excel → значение в БД
ROLE = {"администратор": "administrator", "менеджер": "manager", "клиент": "client"}


def load_pickup_addresses(path):
    """
    Читает файл с адресами пунктов выдачи (первый столбец).
    Возвращает список: индекс 0 = адрес для номера 1 в Excel, индекс 1 = для номера 2 и т.д.
    """
    if not os.path.isfile(path):
        return []
    points_df = pd.read_excel(path, header=None)
    addresses = []
    for i in range(len(points_df)):
        address = str(points_df.iloc[i, 0]).strip()
        if address:
            addresses.append(address)
    print(f"✅ Загружено пунктов выдачи: {len(addresses)}")
    return addresses


def import_users(cur, path):
    """Импортирует пользователей в БД."""
    users = pd.read_excel(path)
    for _, row in users.iterrows():
        login = str(row.get("Логин", "") or "").strip()
        if not login:
            continue
        role_ru = str(row.get("Роль сотрудника", "клиент") or "клиент").strip().lower()
        role = ROLE.get(role_ru, role_ru)
        cur.execute(
            """
            INSERT INTO users (full_name, login, user_password, role)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (login) DO NOTHING;
            """,
            (str(row.get("ФИО", "") or ""), login, str(row.get("Пароль", "") or ""), role),
        )
    print(f"✅ Импортировано пользователей: {len(users)}")
    return len(users)


def import_products(cur, path):
    """Импортирует товары в БД."""
    products = pd.read_excel(path)
    for _, row in products.iterrows():
        name = row.get("Наименование товара")
        if pd.isna(name) or not str(name).strip():
            continue
        photo_path = row.get("Фото")
        if pd.isna(photo_path) or not str(photo_path).strip():
            photo_path = "picture.png"
        else:
            photo_path = str(photo_path).strip()
        price = row.get("Цена")
        price = float(price) if price is not None and not pd.isna(price) else 0
        discount = row.get("Действующая скидка")
        discount = float(discount) if discount is not None and not pd.isna(discount) else 0
        qty = row.get("Кол-во на складе")
        qty = int(float(qty)) if qty is not None and not pd.isna(qty) else 0
        cur.execute(
            """
            INSERT INTO products (
                article, product_name, unit, price, supplier, manufacturer,
                category, discount, stock_quantity, description, photo
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """,
            (
                row.get("Артикул"),
                str(name).strip(),
                row.get("Единица измерения") or "шт.",
                price,
                row.get("Поставщик"),
                row.get("Производитель"),
                row.get("Категория товара"),
                discount,
                qty,
                row.get("Описание товара"),
                photo_path,
            ),
        )
    print(f"✅ Импортировано товаров: {len(products)}")
    return len(products)


def import_orders(cur, path, pickup_addresses):
    """
    Импортирует заказы в БД.
    pickup_addresses — список адресов (индекс 0 = номер 1 в Excel). В столбце «Адрес пункта выдачи» может быть число 1, 2… — подставляется адрес из списка.
    """
    orders = pd.read_excel(path)
    cur.execute("SELECT user_id, full_name FROM users")
    user_by_name = {str(fn).strip().lower(): uid for uid, fn in cur.fetchall() if fn}
    imported = 0

    for _, row in orders.iterrows():
        order_date = pd.to_datetime(row["Дата заказа"], errors="coerce")
        if pd.isna(order_date):
            print(f"⏩ Пропуск заказа: неверная дата ({row['Дата заказа']})")
            continue
        order_date = order_date.date()

        delivery_date = pd.to_datetime(row["Дата доставки"], errors="coerce")
        delivery_date = delivery_date.date() if not pd.isna(delivery_date) else None

        user_name = str(row["ФИО авторизированного клиента"]).strip()
        user_id = user_by_name.get(user_name.lower()) if user_name else None
        if user_id is None and pd.notna(row.get("Номер клиента")):
            try:
                user_id = int(float(row["Номер клиента"]))
            except (TypeError, ValueError):
                pass
        if user_id is None:
            print(f"⏩ Пропуск заказа: клиент не найден ({user_name})")
            continue

        pickup_val = row["Адрес пункта выдачи"]
        pickup_str = None
        if pickup_addresses and pickup_val is not None and not pd.isna(pickup_val):
            try:
                idx = int(float(pickup_val))
                if 1 <= idx <= len(pickup_addresses):
                    pickup_str = pickup_addresses[idx - 1]
            except (TypeError, ValueError):
                pickup_str = str(pickup_val).strip() if str(pickup_val).strip() else None
        elif pickup_val is not None and not pd.isna(pickup_val):
            pickup_str = str(pickup_val).strip()

        pickup_code = None
        if pd.notna(row.get("Код для получения")):
            try:
                pickup_code = int(float(row["Код для получения"]))
            except (TypeError, ValueError):
                pass
        status = str(row.get("Статус заказа", "") or "").strip() or None

        cur.execute(
            """
            INSERT INTO orders (order_date, delivery_date, pickup_point, user_id, pickup_code, status)
            VALUES (%s, %s, %s, %s, %s, %s);
            """,
            (order_date, delivery_date, pickup_str, user_id, pickup_code, status),
        )
        imported += 1
    print(f"✅ Импортировано заказов: {imported}")
    return imported


def import_order_items(cur, path):
    """Импортирует позиции заказов в order_items (если есть файл order_items.xlsx)."""
    if not os.path.isfile(path):
        return 0
    order_items = pd.read_excel(path)
    for _, row in order_items.iterrows():
        oid = row.get("Номер заказа")
        pid = row.get("Номер товара")
        if oid is None or pid is None or pd.isna(oid) or pd.isna(pid):
            continue
        try:
            order_id = int(float(oid))
            product_id = int(float(pid))
        except (TypeError, ValueError):
            continue
        qty = row.get("Количество", 1)
        qty = int(float(qty)) if qty is not None and not pd.isna(qty) else 1
        cur.execute(
            "INSERT INTO order_items (order_id, product_id, quantity) VALUES (%s, %s, %s)",
            (order_id, product_id, qty),
        )
    print(f"✅ Импортировано позиций заказов: {len(order_items)}")
    return len(order_items)


def main():
    """Основная функция импорта данных."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    try:
        print("🚀 Начинаем импорт данных...\n")

        # 1. Список адресов пунктов выдачи
        pickup_addresses = load_pickup_addresses(PATH_POINTS)

        # 2. Импорт пользователей
        import_users(cur, PATH_USERS)

        # 3. Импорт товаров
        import_products(cur, PATH_PRODUCTS)

        # 4. Импорт заказов
        import_orders(cur, PATH_ORDERS, pickup_addresses)

        # 5. Импорт позиций заказов (если файл есть)
        import_order_items(cur, PATH_ORDER_ITEMS)

        conn.commit()

        print(f"\n{'='*50}")
        print("🎉 Импорт завершён успешно!")
        print(f"{'='*50}")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Ошибка при импорте: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
