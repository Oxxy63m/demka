# Работа с БД. Запуск — через main.py.
import psycopg2
from psycopg2.extras import RealDictCursor

from App.config import DB_CONFIG

PRODUCT_SELECT = (
    "SELECT p.product_id, p.article, p.product_name, c.category_name, p.description, m.manufacturer_name, "
    "s.supplier_name, p.price, u.unit_name, p.stock_quantity, p.discount, p.photo "
    "FROM products p LEFT JOIN categories c ON p.category_id = c.category_id "
    "LEFT JOIN manufacturers m ON p.manufacturer_id = m.manufacturer_id "
    "LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id LEFT JOIN units u ON p.unit_id = u.unit_id"
)


def _fetch_column(sql, params=()):
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return [row[0] for row in cur.fetchall()]


def _with_cursor(connection, func, *args):
    cur = connection.cursor()
    try:
        return func(cur, *args)
    finally:
        cur.close()


def auth_user(login, password):
    """Проверка логина и пароля. Возвращает user (user_id, login, full_name, role_name) или None."""
    login, password = (login or "").strip(), (password or "").strip()
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT u.user_id, u.login, u.full_name, r.role_name FROM users u JOIN roles r ON u.role_id = r.role_id "
                "WHERE TRIM(u.login) = %s AND TRIM(u.user_password) = %s", (login, password),
            )
            row = cur.fetchone()
    if row:
        row["id"] = row["user_id"]
    return row


def get_products_all(search_text="", supplier_name=None, order_by_quantity=None):
    """Список товаров: фильтр по поиску, поставщику, сортировка по количеству."""
    query = PRODUCT_SELECT + " WHERE 1=1"
    params = []
    if search_text and search_text.strip():
        q = "%" + search_text.strip() + "%"
        query += " AND (p.article ILIKE %s OR p.product_name ILIKE %s OR p.description ILIKE %s OR c.category_name ILIKE %s OR m.manufacturer_name ILIKE %s OR s.supplier_name ILIKE %s OR u.unit_name ILIKE %s)"
        params = [q] * 7
    if supplier_name:
        query += " AND s.supplier_name = %s"
        params.append(supplier_name)
    if order_by_quantity == "asc":
        query += " ORDER BY p.stock_quantity ASC"
    elif order_by_quantity == "desc":
        query += " ORDER BY p.stock_quantity DESC"
    else:
        query += " ORDER BY p.product_id"
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchall()


def get_product_by_id(product_id):
    """Товар по id (словарь или None)."""
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(PRODUCT_SELECT + " WHERE p.product_id = %s", (product_id,))
            return cur.fetchone()


def get_supplier_names():
    """Названия поставщиков для фильтра (из БД)."""
    return _fetch_column("SELECT supplier_name FROM suppliers ORDER BY supplier_name")


def get_category_names():
    """Категории для формы товара (из БД)."""
    return _fetch_column("SELECT category_name FROM categories ORDER BY category_name")


def get_manufacturer_names():
    """Производители для формы товара (из БД)."""
    return _fetch_column("SELECT manufacturer_name FROM manufacturers ORDER BY manufacturer_name")


def _get_or_create_supplier_id(cursor, supplier_name):
    if not supplier_name or not str(supplier_name).strip():
        return None
    supplier_name = str(supplier_name).strip()
    cursor.execute("SELECT supplier_id FROM suppliers WHERE supplier_name = %s", (supplier_name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute("INSERT INTO suppliers (supplier_name) VALUES (%s) RETURNING supplier_id", (supplier_name,))
    return cursor.fetchone()[0]


def _get_or_create_manufacturer_id(cursor, manufacturer_name):
    if not manufacturer_name or not str(manufacturer_name).strip():
        return None
    manufacturer_name = str(manufacturer_name).strip()
    cursor.execute("SELECT manufacturer_id FROM manufacturers WHERE manufacturer_name = %s", (manufacturer_name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute("INSERT INTO manufacturers (manufacturer_name) VALUES (%s) RETURNING manufacturer_id", (manufacturer_name,))
    return cursor.fetchone()[0]


def _get_or_create_category_id(cursor, category_name):
    if not category_name or not str(category_name).strip():
        return None
    category_name = str(category_name).strip()
    cursor.execute("SELECT category_id FROM categories WHERE category_name = %s", (category_name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute("INSERT INTO categories (category_name) VALUES (%s) RETURNING category_id", (category_name,))
    return cursor.fetchone()[0]


def _get_or_create_unit_id(cursor, unit_name):
    if not unit_name or not str(unit_name).strip():
        return None
    unit_name = str(unit_name).strip()
    cursor.execute("SELECT unit_id FROM units WHERE unit_name = %s", (unit_name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute("INSERT INTO units (unit_name) VALUES (%s) RETURNING unit_id", (unit_name,))
    return cursor.fetchone()[0]


def product_in_orders(product_id):
    """Товар участвует в заказе (нельзя удалить)."""
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM order_items WHERE product_id = %s LIMIT 1", (product_id,))
            return cur.fetchone() is not None


def insert_product(data):
    """Добавить товар. data: article, product_name, unit, price, supplier, manufacturer, category, discount, stock_quantity, description, photo. Возвращает id."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    article = (data.get("article") or "").strip() or "TMP"
    cur.execute(
        "INSERT INTO products (article, product_name, unit_id, price, supplier_id, manufacturer_id, category_id, discount, stock_quantity, description, photo) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING product_id",
        (
            article,
            data.get("product_name"),
            _get_or_create_unit_id(cur, data.get("unit")),
            data.get("price"),
            _get_or_create_supplier_id(cur, data.get("supplier")),
            _get_or_create_manufacturer_id(cur, data.get("manufacturer")),
            _get_or_create_category_id(cur, data.get("category")),
            data.get("discount"),
            data.get("stock_quantity"),
            data.get("description"),
            data.get("photo"),
        ),
    )
    pid = cur.fetchone()[0]
    if article == "TMP":
        cur.execute("UPDATE products SET article = %s WHERE product_id = %s", ("ART-" + str(pid), pid))
    conn.commit()
    cur.close()
    conn.close()
    return pid


def update_product(product_id, data):
    """Обновить товар по id (поля как в insert_product)."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    article = (data.get("article") or "").strip() or ("ART-" + str(product_id))
    cur.execute(
        "UPDATE products SET article=%s, product_name=%s, unit_id=%s, price=%s, supplier_id=%s, manufacturer_id=%s, category_id=%s, discount=%s, stock_quantity=%s, description=%s, photo=%s WHERE product_id=%s",
        (
            article,
            data.get("product_name"),
            _get_or_create_unit_id(cur, data.get("unit")),
            data.get("price"),
            _get_or_create_supplier_id(cur, data.get("supplier")),
            _get_or_create_manufacturer_id(cur, data.get("manufacturer")),
            _get_or_create_category_id(cur, data.get("category")),
            data.get("discount"),
            data.get("stock_quantity"),
            data.get("description"),
            data.get("photo"),
            product_id,
        ),
    )
    conn.commit()
    cur.close()
    conn.close()


def delete_product(product_id):
    """Удалить товар по id."""
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM products WHERE product_id = %s", (product_id,))
        conn.commit()


def _get_or_create_status_id(cursor, status_name):
    if not status_name or not str(status_name).strip():
        cursor.execute("SELECT status_id FROM order_statuses WHERE status_name = 'новый' LIMIT 1")
        row = cursor.fetchone()
        return row[0] if row else None
    status_name = str(status_name).strip()
    cursor.execute("SELECT status_id FROM order_statuses WHERE status_name = %s", (status_name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute("INSERT INTO order_statuses (status_name) VALUES (%s) RETURNING status_id", (status_name,))
    return cursor.fetchone()[0]


def _get_or_create_pickup_point_id(cursor, pickup_address):
    if not pickup_address or not str(pickup_address).strip():
        return None
    pickup_address = str(pickup_address).strip()
    cursor.execute("SELECT pickup_point_id FROM pickup_points WHERE pickup_address = %s", (pickup_address,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute("INSERT INTO pickup_points (pickup_address) VALUES (%s) RETURNING pickup_point_id", (pickup_address,))
    return cursor.fetchone()[0]


def get_orders_all():
    """Список заказов (id, order_date, delivery_date, pickup_point_address, status_name, user_name, user_id)."""
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT o.order_id AS id, o.order_date, o.delivery_date, pp.pickup_address AS pickup_point_address, st.status_name, o.user_id, u.full_name AS user_name "
                "FROM orders o JOIN users u ON o.user_id = u.user_id "
                "LEFT JOIN order_statuses st ON o.status_id = st.status_id LEFT JOIN pickup_points pp ON o.pickup_point_id = pp.pickup_point_id "
                "ORDER BY o.order_date DESC, o.order_id DESC"
            )
            rows = cur.fetchall()
    for row in rows:
        row["order_article"] = ""
    return rows


def get_order_by_id(order_id):
    """Заказ по id (словарь или None)."""
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT o.order_id AS id, o.order_date, o.delivery_date, pp.pickup_address AS pickup_point_address, st.status_name, o.user_id "
                "FROM orders o LEFT JOIN order_statuses st ON o.status_id = st.status_id LEFT JOIN pickup_points pp ON o.pickup_point_id = pp.pickup_point_id WHERE o.order_id = %s",
                (order_id,),
            )
            row = cur.fetchone()
    if row:
        row["order_article"] = ""
    return row


def get_users_list():
    """Пользователи для выбора в заказе (user_id, full_name) из БД."""
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT user_id, full_name FROM users ORDER BY full_name")
            return cur.fetchall()


def get_order_statuses():
    """Статусы заказа из БД (для форм и корзины)."""
    return _fetch_column("SELECT status_name FROM order_statuses ORDER BY status_name")


def get_pickup_addresses():
    """Адреса пунктов выдачи из БД (для форм и корзины)."""
    return _fetch_column("SELECT pickup_address FROM pickup_points ORDER BY pickup_address")


def insert_order(data):
    """Добавить заказ. data: order_date, delivery_date, pickup_point, user_id, status, pickup_code. Возвращает order_id."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO orders (order_date, delivery_date, pickup_point_id, user_id, pickup_code, status_id) VALUES (%s, %s, %s, %s, %s, %s) RETURNING order_id",
        (
            data.get("order_date"),
            data.get("delivery_date"),
            _get_or_create_pickup_point_id(cur, data.get("pickup_point")),
            data.get("user_id"),
            data.get("pickup_code"),
            _get_or_create_status_id(cur, data.get("status")),
        ),
    )
    oid = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return oid


def update_order(order_id, data):
    """Обновить заказ по id (order_date, delivery_date, pickup_point, user_id, status)."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(
        "UPDATE orders SET order_date=%s, delivery_date=%s, pickup_point_id=%s, user_id=%s, status_id=%s WHERE order_id=%s",
        (
            data.get("order_date"),
            data.get("delivery_date"),
            _get_or_create_pickup_point_id(cur, data.get("pickup_point")),
            data.get("user_id"),
            _get_or_create_status_id(cur, data.get("status")),
            order_id,
        ),
    )
    conn.commit()
    cur.close()
    conn.close()


def delete_order(order_id):
    """Удалить заказ по id."""
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM orders WHERE order_id = %s", (order_id,))
        conn.commit()


def get_or_create_role_id(connection, role_name):
    """role_id по имени роли (для импорта); при отсутствии — вставить."""
    if not role_name or not str(role_name).strip():
        return None
    role_name = str(role_name).strip()
    cur = connection.cursor()
    cur.execute("SELECT role_id FROM roles WHERE role_name = %s", (role_name,))
    row = cur.fetchone()
    if row:
        cur.close()
        return row[0]
    cur.execute("INSERT INTO roles (role_name) VALUES (%s) ON CONFLICT (role_name) DO NOTHING", (role_name,))
    cur.execute("SELECT role_id FROM roles WHERE role_name = %s", (role_name,))
    row = cur.fetchone()
    cur.close()
    return row[0] if row else None


def get_or_create_supplier_id_conn(connection, name):
    return _with_cursor(connection, _get_or_create_supplier_id, name)


def get_or_create_manufacturer_id_conn(connection, name):
    return _with_cursor(connection, _get_or_create_manufacturer_id, name)


def get_or_create_category_id_conn(connection, name):
    return _with_cursor(connection, _get_or_create_category_id, name)


def get_or_create_unit_id_conn(connection, code_or_name):
    return _with_cursor(connection, _get_or_create_unit_id, code_or_name)


def get_or_create_pickup_point_id_conn(connection, address):
    return _with_cursor(connection, _get_or_create_pickup_point_id, address)


def get_or_create_status_id_conn(connection, name):
    return _with_cursor(connection, _get_or_create_status_id, name or "новый")


def insert_order_items(order_id, items):
    """Добавить позиции заказа. items: [{product_id, quantity, unit_price}, ...]."""
    if not items:
        return
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            for it in items:
                cur.execute(
                    "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (%s, %s, %s, %s)",
                    (order_id, it["product_id"], it["quantity"], float(it.get("unit_price", 0))),
                )
        conn.commit()
