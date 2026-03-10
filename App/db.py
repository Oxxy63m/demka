# Работа с базой данных: вход пользователя, товары, заказы, справочники.
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
    """Проверяет логин и пароль. Возвращает словарь пользователя (user_id, login, full_name, role_name) или None."""
    login = (login or "").strip()
    password = (password or "").strip()
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute(
            "SELECT u.user_id, u.login, u.full_name, r.role_name FROM users u "
            "JOIN roles r ON u.role_id = r.role_id WHERE TRIM(u.login) = %s AND TRIM(u.user_password) = %s",
            (login, password),
        )
    except Exception:
        cursor.execute(
            "SELECT u.user_id, u.login, u.full_name, r.name AS role_name FROM users u "
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
    """Список товаров с фильтром по поиску, поставщику и сортировке по количеству."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        query = (
            "SELECT p.id, p.article, p.product_name, c.category_name, p.description, m.manufacturer_name, "
            "s.supplier_name, p.price, u.unit_code, p.stock_quantity, p.discount, p.photo "
            "FROM products p "
            "LEFT JOIN categories c ON p.category_id = c.category_id "
            "LEFT JOIN manufacturers m ON p.manufacturer_id = m.manufacturer_id "
            "LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id "
            "LEFT JOIN units u ON p.unit_id = u.unit_id WHERE 1=1"
        )
        params = []
        if search_text and search_text.strip():
            q = "%" + search_text.strip() + "%"
            query += " AND (p.article ILIKE %s OR p.product_name ILIKE %s OR p.description ILIKE %s OR c.category_name ILIKE %s OR m.manufacturer_name ILIKE %s OR s.supplier_name ILIKE %s OR u.unit_code ILIKE %s)"
            params = [q] * 7
        if supplier_name:
            query += " AND s.supplier_name = %s"
            params.append(supplier_name)
        if order_by_quantity == "asc":
            query += " ORDER BY p.stock_quantity ASC"
        elif order_by_quantity == "desc":
            query += " ORDER BY p.stock_quantity DESC"
        else:
            query += " ORDER BY p.id"
        cur.execute(query, params)
        rows = cur.fetchall()
    except Exception:
        # Старая схема: в products колонки unit, supplier, manufacturer, category (без справочников)
        query = "SELECT id, article, product_name, category AS category_name, description, manufacturer AS manufacturer_name, supplier AS supplier_name, price, unit AS unit_code, stock_quantity, discount, photo FROM products WHERE 1=1"
        params = []
        if search_text and search_text.strip():
            q = "%" + search_text.strip() + "%"
            query += " AND (article ILIKE %s OR product_name ILIKE %s OR COALESCE(description,'')::text ILIKE %s OR COALESCE(category,'') ILIKE %s OR COALESCE(manufacturer,'') ILIKE %s OR COALESCE(supplier,'') ILIKE %s OR COALESCE(unit,'') ILIKE %s)"
            params = [q] * 7
        if supplier_name:
            query += " AND supplier = %s"
            params.append(supplier_name)
        if order_by_quantity == "asc":
            query += " ORDER BY stock_quantity ASC"
        elif order_by_quantity == "desc":
            query += " ORDER BY stock_quantity DESC"
        else:
            query += " ORDER BY id"
        cur.execute(query, params)
        rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_product_by_id(product_id):
    """Один товар по id. Возвращает словарь или None."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            "SELECT p.id, p.article, p.product_name, c.category_name, p.description, m.manufacturer_name, "
            "s.supplier_name, p.price, u.unit_code, p.stock_quantity, p.discount, p.photo "
            "FROM products p LEFT JOIN categories c ON p.category_id = c.category_id "
            "LEFT JOIN manufacturers m ON p.manufacturer_id = m.manufacturer_id "
            "LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id "
            "LEFT JOIN units u ON p.unit_id = u.unit_id WHERE p.id = %s",
            (product_id,),
        )
        row = cur.fetchone()
    except Exception:
        cur.execute(
            "SELECT id, article, product_name, category AS category_name, description, manufacturer AS manufacturer_name, supplier AS supplier_name, price, unit AS unit_code, stock_quantity, discount, photo FROM products WHERE id = %s",
            (product_id,),
        )
        row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def get_supplier_names():
    """Список названий поставщиков для фильтра."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        cur.execute("SELECT supplier_name FROM suppliers ORDER BY supplier_name")
        out = [r[0] for r in cur.fetchall()]
    except Exception:
        cur.execute("SELECT DISTINCT supplier FROM products WHERE supplier IS NOT NULL AND supplier != '' ORDER BY supplier")
        out = [r[0] for r in cur.fetchall()]
    cur.close()
    conn.close()
    return out


def get_category_names():
    """Список категорий для формы товара."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        cur.execute("SELECT category_name FROM categories ORDER BY category_name")
        out = [r[0] for r in cur.fetchall()]
    except Exception:
        cur.execute("SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND category != '' ORDER BY category")
        out = [r[0] for r in cur.fetchall()]
    cur.close()
    conn.close()
    return out


def get_manufacturer_names():
    """Список производителей для формы товара."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        cur.execute("SELECT manufacturer_name FROM manufacturers ORDER BY manufacturer_name")
        out = [r[0] for r in cur.fetchall()]
    except Exception:
        cur.execute("SELECT DISTINCT manufacturer FROM products WHERE manufacturer IS NOT NULL AND manufacturer != '' ORDER BY manufacturer")
        out = [r[0] for r in cur.fetchall()]
    cur.close()
    conn.close()
    return out


def get_unit_names():
    """Список единиц измерения для формы товара."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        cur.execute("SELECT unit_code FROM units ORDER BY unit_code")
        out = [r[0] for r in cur.fetchall()]
    except Exception:
        cur.execute("SELECT DISTINCT unit FROM products WHERE unit IS NOT NULL AND unit != '' ORDER BY unit")
        out = [r[0] for r in cur.fetchall()]
    cur.close()
    conn.close()
    return out


def _get_or_create_supplier_id(cursor, name):
    if not name or not str(name).strip():
        return None
    name = str(name).strip()
    try:
        cursor.execute("SELECT supplier_id FROM suppliers WHERE supplier_name = %s", (name,))
    except Exception:
        cursor.execute("SELECT supplier_id FROM suppliers WHERE name = %s", (name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    try:
        cursor.execute("INSERT INTO suppliers (supplier_name) VALUES (%s) RETURNING supplier_id", (name,))
    except Exception:
        cursor.execute("INSERT INTO suppliers (name) VALUES (%s) RETURNING supplier_id", (name,))
    return cursor.fetchone()[0]


def _get_or_create_manufacturer_id(cursor, name):
    if not name or not str(name).strip():
        return None
    name = str(name).strip()
    try:
        cursor.execute("SELECT manufacturer_id FROM manufacturers WHERE manufacturer_name = %s", (name,))
    except Exception:
        cursor.execute("SELECT manufacturer_id FROM manufacturers WHERE name = %s", (name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    try:
        cursor.execute("INSERT INTO manufacturers (manufacturer_name) VALUES (%s) RETURNING manufacturer_id", (name,))
    except Exception:
        cursor.execute("INSERT INTO manufacturers (name) VALUES (%s) RETURNING manufacturer_id", (name,))
    return cursor.fetchone()[0]


def _get_or_create_category_id(cursor, name):
    if not name or not str(name).strip():
        return None
    name = str(name).strip()
    try:
        cursor.execute("SELECT category_id FROM categories WHERE category_name = %s", (name,))
    except Exception:
        cursor.execute("SELECT category_id FROM categories WHERE name = %s", (name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    try:
        cursor.execute("INSERT INTO categories (category_name) VALUES (%s) RETURNING category_id", (name,))
    except Exception:
        cursor.execute("INSERT INTO categories (name) VALUES (%s) RETURNING category_id", (name,))
    return cursor.fetchone()[0]


def _get_or_create_unit_id(cursor, code_or_name):
    if not code_or_name or not str(code_or_name).strip():
        return None
    val = str(code_or_name).strip()
    try:
        cursor.execute("SELECT unit_id FROM units WHERE unit_code = %s OR unit_name = %s", (val, val))
    except Exception:
        cursor.execute("SELECT unit_id FROM units WHERE code = %s OR name = %s", (val, val))
    row = cursor.fetchone()
    if row:
        return row[0]
    try:
        cursor.execute("INSERT INTO units (unit_code, unit_name) VALUES (%s, %s) RETURNING unit_id", (val, val))
    except Exception:
        cursor.execute("INSERT INTO units (code, name) VALUES (%s, %s) RETURNING unit_id", (val, val))
    return cursor.fetchone()[0]


def product_in_orders(product_id):
    """Есть ли товар хотя бы в одном заказе (нельзя удалить)."""
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()
    cursor.execute("SELECT 1 FROM order_items WHERE product_id = %s LIMIT 1", (product_id,))
    found_row = cursor.fetchone()
    cursor.close()
    connection.close()
    return found_row is not None


def insert_product(data):
    """Добавляет товар. data: article, product_name, unit, price, supplier, manufacturer, category, discount, stock_quantity, description, photo. Возвращает id."""
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()
    supplier_id = _get_or_create_supplier_id(cursor, data.get("supplier"))
    manufacturer_id = _get_or_create_manufacturer_id(cursor, data.get("manufacturer"))
    category_id = _get_or_create_category_id(cursor, data.get("category"))
    unit_id = _get_or_create_unit_id(cursor, data.get("unit"))
    article = (data.get("article") or "").strip()
    if not article:
        article = "TMP"
    cursor.execute(
        "INSERT INTO products (article, product_name, unit_id, price, supplier_id, manufacturer_id, category_id, discount, stock_quantity, description, photo) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
        (
            article,
            data.get("product_name"),
            unit_id,
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
    if article == "TMP":
        cursor.execute("UPDATE products SET article = %s WHERE id = %s", ("ART-" + str(inserted_product_id), inserted_product_id))
    connection.commit()
    cursor.close()
    connection.close()
    return inserted_product_id


def update_product(product_id, data):
    """Обновляет товар по id. data — те же поля, что у insert_product."""
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()
    supplier_id = _get_or_create_supplier_id(cursor, data.get("supplier"))
    manufacturer_id = _get_or_create_manufacturer_id(cursor, data.get("manufacturer"))
    category_id = _get_or_create_category_id(cursor, data.get("category"))
    unit_id = _get_or_create_unit_id(cursor, data.get("unit"))
    article = (data.get("article") or "").strip()
    if not article:
        article = "ART-" + str(product_id)
    cursor.execute(
        "UPDATE products SET article=%s, product_name=%s, unit_id=%s, price=%s, supplier_id=%s, manufacturer_id=%s, category_id=%s, "
        "discount=%s, stock_quantity=%s, description=%s, photo=%s WHERE id=%s",
        (
            article,
            data.get("product_name"),
            unit_id,
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
    """Удаляет товар по id."""
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()
    cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
    connection.commit()
    cursor.close()
    connection.close()


# --- Заказы ---

def _get_or_create_status_id(cursor, name):
    if not name or not str(name).strip():
        try:
            cursor.execute("SELECT status_id FROM order_statuses WHERE status_name = 'новый' LIMIT 1")
        except Exception:
            cursor.execute("SELECT status_id FROM order_statuses WHERE name = 'новый' LIMIT 1")
        row = cursor.fetchone()
        return row[0] if row else None
    name = str(name).strip()
    try:
        cursor.execute("SELECT status_id FROM order_statuses WHERE status_name = %s", (name,))
    except Exception:
        cursor.execute("SELECT status_id FROM order_statuses WHERE name = %s", (name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    try:
        cursor.execute("INSERT INTO order_statuses (status_name) VALUES (%s) RETURNING status_id", (name,))
    except Exception:
        cursor.execute("INSERT INTO order_statuses (name) VALUES (%s) RETURNING status_id", (name,))
    return cursor.fetchone()[0]


def _get_or_create_pickup_point_id(cursor, address):
    if not address or not str(address).strip():
        return None
    address = str(address).strip()
    try:
        cursor.execute("SELECT pickup_point_id FROM pickup_points WHERE pickup_address = %s", (address,))
    except Exception:
        cursor.execute("SELECT pickup_point_id FROM pickup_points WHERE address = %s", (address,))
    row = cursor.fetchone()
    if row:
        return row[0]
    try:
        cursor.execute("INSERT INTO pickup_points (pickup_address) VALUES (%s) RETURNING pickup_point_id", (address,))
    except Exception:
        cursor.execute("INSERT INTO pickup_points (address) VALUES (%s) RETURNING pickup_point_id", (address,))
    return cursor.fetchone()[0]


def get_orders_all():
    """Возвращает список всех заказов (словари с id, order_date, pickup_point_address, status_name, user_name и т.д.)."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            "SELECT o.order_id AS id, o.order_date, o.delivery_date, pp.pickup_address AS pickup_point_address, "
            "st.status_name, o.user_id, u.full_name AS user_name "
            "FROM orders o JOIN users u ON o.user_id = u.user_id "
            "LEFT JOIN order_statuses st ON o.status_id = st.status_id "
            "LEFT JOIN pickup_points pp ON o.pickup_point_id = pp.pickup_point_id "
            "ORDER BY o.order_date DESC, o.order_id DESC"
        )
        rows = cur.fetchall()
        for r in rows:
            r["order_article"] = ""
    except Exception:
        cur.execute(
            "SELECT o.order_id AS id, o.order_date, o.delivery_date, o.pickup_point AS pickup_point_address, o.status AS status_name, o.user_id, u.full_name AS user_name "
            "FROM orders o JOIN users u ON o.user_id = u.user_id ORDER BY o.order_date DESC, o.order_id DESC"
        )
        rows = cur.fetchall()
        for r in rows:
            r["order_article"] = r.get("order_article") or ""
    cur.close()
    conn.close()
    return rows


def get_order_by_id(order_id):
    """Возвращает один заказ по id (словарь) или None."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            "SELECT o.order_id AS id, o.order_date, o.delivery_date, pp.pickup_address AS pickup_point_address, st.status_name, o.user_id "
            "FROM orders o LEFT JOIN order_statuses st ON o.status_id = st.status_id "
            "LEFT JOIN pickup_points pp ON o.pickup_point_id = pp.pickup_point_id WHERE o.order_id = %s",
            (order_id,),
        )
        row = cur.fetchone()
        if row:
            row["order_article"] = ""
    except Exception:
        cur.execute(
            "SELECT order_id AS id, order_date, delivery_date, pickup_point AS pickup_point_address, status AS status_name, user_id FROM orders WHERE order_id = %s",
            (order_id,),
        )
        row = cur.fetchone()
        if row:
            row["order_article"] = row.get("order_article") or ""
    cur.close()
    conn.close()
    return row


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
    """Добавляет заказ в БД. data: order_date, delivery_date, pickup_point, user_id, status, pickup_code (необяз.). Возвращает order_id."""
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()
    status_id = _get_or_create_status_id(cursor, data.get("status"))
    pickup_point_id = _get_or_create_pickup_point_id(cursor, data.get("pickup_point"))
    cursor.execute(
        "INSERT INTO orders (order_date, delivery_date, pickup_point_id, user_id, pickup_code, status_id) "
        "VALUES (%s, %s, %s, %s, %s, %s) RETURNING order_id",
        (
            data.get("order_date"),
            data.get("delivery_date"),
            pickup_point_id,
            data.get("user_id"),
            data.get("pickup_code"),
            status_id,
        ),
    )
    inserted_order_id = cursor.fetchone()[0]
    connection.commit()
    cursor.close()
    connection.close()
    return inserted_order_id


def update_order(order_id, data):
    """Обновляет заказ по id. data: order_date, delivery_date, pickup_point, user_id, status."""
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()
    status_id = _get_or_create_status_id(cursor, data.get("status"))
    pickup_point_id = _get_or_create_pickup_point_id(cursor, data.get("pickup_point"))
    cursor.execute(
        "UPDATE orders SET order_date=%s, delivery_date=%s, pickup_point_id=%s, user_id=%s, status_id=%s WHERE order_id=%s",
        (
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
    """Удаляет заказ по id."""
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
    try:
        cursor.execute("SELECT role_id FROM roles WHERE role_name = %s", (name,))
    except Exception:
        cursor.execute("SELECT role_id FROM roles WHERE name = %s", (name,))
    row = cursor.fetchone()
    if row:
        cursor.close()
        return row[0]
    try:
        cursor.execute("INSERT INTO roles (role_name) VALUES (%s) ON CONFLICT (role_name) DO NOTHING", (name,))
        cursor.execute("SELECT role_id FROM roles WHERE role_name = %s", (name,))
    except Exception:
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


def get_or_create_unit_id_conn(connection, code_or_name):
    cursor = connection.cursor()
    try:
        return _get_or_create_unit_id(cursor, code_or_name)
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
    """Добавляет позиции заказа. items: список словарей с ключами product_id, quantity, unit_price (цена за единицу)."""
    if not items:
        return
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()
    for it in items:
        unit_price = float(it.get("unit_price", 0))
        cursor.execute(
            "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (%s, %s, %s, %s)",
            (order_id, it["product_id"], it["quantity"], unit_price),
        )
    connection.commit()
    cursor.close()
    connection.close()
