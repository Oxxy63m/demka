# App/db.py — все функции работы с БД: авторизация, товары (список/по id), поставщики, проверка в заказах, вставка/обновление/удаление
import os
import sys

# Чтобы работало и при запуске python App/db.py, и при импорте из main.py
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

import psycopg2
from psycopg2.extras import RealDictCursor

from App.config import DB_CONFIG


def auth_user(login, password):
    login = (login or "").strip()
    password = (password or "").strip()
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        "SELECT u.user_id, u.login, u.full_name, r.name AS role FROM users u "
        "JOIN roles r ON u.role_id = r.role_id WHERE TRIM(u.login) = %s AND TRIM(u.user_password) = %s",
        (login, password),
    )
    user_row = cursor.fetchone()
    cursor.close()
    connection.close()
    if user_row:
        user_row["id"] = user_row["user_id"]
    return user_row


def get_products_all(search_text="", supplier_name=None, order_by_quantity=None):
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    query = (
        "SELECT p.id, p.article, p.product_name, c.name AS category, p.description, m.name AS manufacturer, "
        "s.name AS supplier, p.price, p.unit, p.stock_quantity, p.discount, p.photo "
        "FROM products p "
        "LEFT JOIN categories c ON p.category_id = c.category_id "
        "LEFT JOIN manufacturers m ON p.manufacturer_id = m.manufacturer_id "
        "LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id WHERE 1=1"
    )
    query_params = []
    if search_text and search_text.strip():
        search_pattern = "%" + search_text.strip() + "%"
        query += " AND (p.article ILIKE %s OR p.product_name ILIKE %s OR p.description ILIKE %s OR c.name ILIKE %s OR m.name ILIKE %s OR s.name ILIKE %s OR p.unit ILIKE %s)"
        query_params = [search_pattern, search_pattern, search_pattern, search_pattern, search_pattern, search_pattern, search_pattern]
    if supplier_name:
        query += " AND s.name = %s"
        query_params.append(supplier_name)
    if order_by_quantity == "asc":
        query += " ORDER BY p.stock_quantity ASC"
    elif order_by_quantity == "desc":
        query += " ORDER BY p.stock_quantity DESC"
    else:
        query += " ORDER BY p.id"
    cursor.execute(query, query_params)
    result_rows = cursor.fetchall()
    cursor.close()
    connection.close()
    return result_rows


def get_product_by_id(product_id):
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        "SELECT p.id, p.article, p.product_name, c.name AS category, p.description, m.name AS manufacturer, "
        "s.name AS supplier, p.price, p.unit, p.stock_quantity, p.discount, p.photo "
        "FROM products p LEFT JOIN categories c ON p.category_id = c.category_id "
        "LEFT JOIN manufacturers m ON p.manufacturer_id = m.manufacturer_id "
        "LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id WHERE p.id = %s",
        (product_id,),
    )
    product_row = cursor.fetchone()
    cursor.close()
    connection.close()
    return product_row


def get_supplier_names():
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()
    cursor.execute("SELECT name FROM suppliers ORDER BY name")
    result_rows = cursor.fetchall()
    cursor.close()
    connection.close()
    return [r[0] for r in result_rows]


def get_category_names():
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()
    cursor.execute("SELECT name FROM categories ORDER BY name")
    result_rows = cursor.fetchall()
    cursor.close()
    connection.close()
    return [r[0] for r in result_rows]


def get_manufacturer_names():
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()
    cursor.execute("SELECT name FROM manufacturers ORDER BY name")
    result_rows = cursor.fetchall()
    cursor.close()
    connection.close()
    return [r[0] for r in result_rows]


def _get_or_create_supplier_id(cursor, name):
    if not name or not str(name).strip():
        return None
    name = str(name).strip()
    cursor.execute("SELECT supplier_id FROM suppliers WHERE name = %s", (name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute("INSERT INTO suppliers (name) VALUES (%s) RETURNING supplier_id", (name,))
    return cursor.fetchone()[0]


def _get_or_create_manufacturer_id(cursor, name):
    if not name or not str(name).strip():
        return None
    name = str(name).strip()
    cursor.execute("SELECT manufacturer_id FROM manufacturers WHERE name = %s", (name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute("INSERT INTO manufacturers (name) VALUES (%s) RETURNING manufacturer_id", (name,))
    return cursor.fetchone()[0]


def _get_or_create_category_id(cursor, name):
    if not name or not str(name).strip():
        return None
    name = str(name).strip()
    cursor.execute("SELECT category_id FROM categories WHERE name = %s", (name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute("INSERT INTO categories (name) VALUES (%s) RETURNING category_id", (name,))
    return cursor.fetchone()[0]


def product_in_orders(product_id):
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()
    cursor.execute("SELECT 1 FROM order_items WHERE product_id = %s LIMIT 1", (product_id,))
    found_row = cursor.fetchone()
    cursor.close()
    connection.close()
    return found_row is not None


def insert_product(data):
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()
    supplier_id = _get_or_create_supplier_id(cursor, data.get("supplier"))
    manufacturer_id = _get_or_create_manufacturer_id(cursor, data.get("manufacturer"))
    category_id = _get_or_create_category_id(cursor, data.get("category"))
    cursor.execute(
        "INSERT INTO products (article, product_name, unit, price, supplier_id, manufacturer_id, category_id, discount, stock_quantity, description, photo) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
        (
            data.get("article"),
            data.get("product_name"),
            data.get("unit"),
            data.get("price"),
            supplier_id,
            manufacturer_id,
            category_id,
            data.get("discount"),
            data.get("stock_quantity"),
            data.get("description"),
            data.get("photo"),
        ),
    )
    inserted_product_id = cursor.fetchone()[0]
    connection.commit()
    cursor.close()
    connection.close()
    return inserted_product_id


def update_product(product_id, data):
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()
    supplier_id = _get_or_create_supplier_id(cursor, data.get("supplier"))
    manufacturer_id = _get_or_create_manufacturer_id(cursor, data.get("manufacturer"))
    category_id = _get_or_create_category_id(cursor, data.get("category"))
    cursor.execute(
        "UPDATE products SET article=%s, product_name=%s, unit=%s, price=%s, supplier_id=%s, manufacturer_id=%s, category_id=%s, "
        "discount=%s, stock_quantity=%s, description=%s, photo=%s WHERE id=%s",
        (
            data.get("article"),
            data.get("product_name"),
            data.get("unit"),
            data.get("price"),
            supplier_id,
            manufacturer_id,
            category_id,
            data.get("discount"),
            data.get("stock_quantity"),
            data.get("description"),
            data.get("photo"),
            product_id,
        ),
    )
    connection.commit()
    cursor.close()
    connection.close()


def delete_product(product_id):
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()
    cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
    connection.commit()
    cursor.close()
    connection.close()


# --- Заказы (Модуль 4) ---

_orders_schema_checked = False


def _ensure_order_article_column():
    """Добавить столбец order_article в таблицу orders, если его нет (для БД, созданных по старой схеме)."""
    global _orders_schema_checked
    if _orders_schema_checked:
        return
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS order_article VARCHAR(50);")
        connection.commit()
        cursor.close()
        connection.close()
    except Exception:
        pass
    _orders_schema_checked = True


def _get_or_create_status_id(cursor, name):
    if not name or not str(name).strip():
        cursor.execute("SELECT status_id FROM order_statuses WHERE name = 'новый' LIMIT 1")
        row = cursor.fetchone()
        return row[0] if row else None
    name = str(name).strip()
    cursor.execute("SELECT status_id FROM order_statuses WHERE name = %s", (name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute("INSERT INTO order_statuses (name) VALUES (%s) RETURNING status_id", (name,))
    return cursor.fetchone()[0]


def _get_or_create_pickup_point_id(cursor, address):
    if not address or not str(address).strip():
        return None
    address = str(address).strip()
    cursor.execute("SELECT pickup_point_id FROM pickup_points WHERE address = %s", (address,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute("INSERT INTO pickup_points (address) VALUES (%s) RETURNING pickup_point_id", (address,))
    return cursor.fetchone()[0]


def get_orders_all():
    _ensure_order_article_column()
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        "SELECT o.order_id AS id, o.order_article, o.order_date, o.delivery_date, pp.address AS pickup_point, "
        "st.name AS status, o.user_id, u.full_name AS user_name "
        "FROM orders o JOIN users u ON o.user_id = u.user_id "
        "LEFT JOIN order_statuses st ON o.status_id = st.status_id "
        "LEFT JOIN pickup_points pp ON o.pickup_point_id = pp.pickup_point_id "
        "ORDER BY o.order_date DESC, o.order_id DESC"
    )
    result_rows = cursor.fetchall()
    cursor.close()
    connection.close()
    return result_rows


def get_order_by_id(order_id):
    _ensure_order_article_column()
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        "SELECT o.order_id AS id, o.order_article, o.order_date, o.delivery_date, pp.address AS pickup_point, "
        "st.name AS status, o.user_id FROM orders o "
        "LEFT JOIN order_statuses st ON o.status_id = st.status_id "
        "LEFT JOIN pickup_points pp ON o.pickup_point_id = pp.pickup_point_id WHERE o.order_id = %s",
        (order_id,),
    )
    order_row = cursor.fetchone()
    cursor.close()
    connection.close()
    return order_row


def get_users_list():
    """Список пользователей для выбора в заказе (user_id, full_name)."""
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT user_id, full_name FROM users ORDER BY full_name")
    result_rows = cursor.fetchall()
    cursor.close()
    connection.close()
    return result_rows


def insert_order(data):
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()
    status_id = _get_or_create_status_id(cursor, data.get("status"))
    pickup_point_id = _get_or_create_pickup_point_id(cursor, data.get("pickup_point"))
    cursor.execute(
        "INSERT INTO orders (order_article, order_date, delivery_date, pickup_point_id, user_id, status_id) "
        "VALUES (%s, %s, %s, %s, %s, %s) RETURNING order_id",
        (
            data.get("order_article"),
            data.get("order_date"),
            data.get("delivery_date"),
            pickup_point_id,
            data.get("user_id"),
            status_id,
        ),
    )
    inserted_order_id = cursor.fetchone()[0]
    connection.commit()
    cursor.close()
    connection.close()
    return inserted_order_id


def update_order(order_id, data):
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()
    status_id = _get_or_create_status_id(cursor, data.get("status"))
    pickup_point_id = _get_or_create_pickup_point_id(cursor, data.get("pickup_point"))
    cursor.execute(
        "UPDATE orders SET order_article=%s, order_date=%s, delivery_date=%s, pickup_point_id=%s, user_id=%s, status_id=%s WHERE order_id=%s",
        (
            data.get("order_article"),
            data.get("order_date"),
            data.get("delivery_date"),
            pickup_point_id,
            data.get("user_id"),
            status_id,
            order_id,
        ),
    )
    connection.commit()
    cursor.close()
    connection.close()


def delete_order(order_id):
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()
    cursor.execute("DELETE FROM orders WHERE order_id = %s", (order_id,))
    connection.commit()
    cursor.close()
    connection.close()


def get_product_articles(product_ids):
    """Возвращает словарь {product_id: article} для списка product_ids."""
    if not product_ids:
        return {}
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    ids = list(set(product_ids))
    placeholders = ",".join(["%s"] * len(ids))
    cursor.execute(
        f"SELECT id, article FROM products WHERE id IN ({placeholders})",
        ids,
    )
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    return {r["id"]: (r["article"] or "").strip() or str(r["id"]) for r in rows}


def build_order_article_string(parts):
    """parts: список словарей с ключами product_article, quantity. Возвращает строку вида 'артикул1-2,артикул2-1'."""
    return ",".join(f"{p.get('product_article', '')}-{int(p.get('quantity', 0))}" for p in parts)


def get_or_create_role_id(connection, name):
    """Для импорта: вернуть role_id по имени, при отсутствии — вставить и вернуть."""
    if not name or not str(name).strip():
        return None
    name = str(name).strip()
    cursor = connection.cursor()
    cursor.execute("SELECT role_id FROM roles WHERE name = %s", (name,))
    row = cursor.fetchone()
    if row:
        cursor.close()
        return row[0]
    cursor.execute("INSERT INTO roles (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (name,))
    cursor.execute("SELECT role_id FROM roles WHERE name = %s", (name,))
    row = cursor.fetchone()
    cursor.close()
    return row[0] if row else None


def get_or_create_supplier_id_conn(connection, name):
    cursor = connection.cursor()
    try:
        return _get_or_create_supplier_id(cursor, name)
    finally:
        cursor.close()


def get_or_create_manufacturer_id_conn(connection, name):
    cursor = connection.cursor()
    try:
        return _get_or_create_manufacturer_id(cursor, name)
    finally:
        cursor.close()


def get_or_create_category_id_conn(connection, name):
    cursor = connection.cursor()
    try:
        return _get_or_create_category_id(cursor, name)
    finally:
        cursor.close()


def get_or_create_pickup_point_id_conn(connection, address):
    cursor = connection.cursor()
    try:
        return _get_or_create_pickup_point_id(cursor, address)
    finally:
        cursor.close()


def get_or_create_status_id_conn(connection, name):
    cursor = connection.cursor()
    try:
        return _get_or_create_status_id(cursor, name or "новый")
    finally:
        cursor.close()


def insert_order_items(order_id, items):
    """items: список словарей с ключами product_id, quantity."""
    if not items:
        return
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()
    for it in items:
        cursor.execute(
            "INSERT INTO order_items (order_id, product_id, quantity) VALUES (%s, %s, %s)",
            (order_id, it["product_id"], it["quantity"]),
        )
    connection.commit()
    cursor.close()
    connection.close()
