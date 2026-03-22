import psycopg2
from psycopg2.extras import RealDictCursor

from App.config import DB_CONFIG


def q(sql, params=(), fetch=None, dict_cursor=False):
    cursor_factory = RealDictCursor if dict_cursor else None
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor(cursor_factory=cursor_factory) as cur:
            cur.execute(sql, params)
            if fetch == "one":
                return cur.fetchone()
            if fetch == "all":
                return cur.fetchall()
            return None


def _fetch_column(sql, params=()):
    rows = q(sql, params=params, fetch="all", dict_cursor=False) or []
    result = []
    for row in rows:
        result.append(row[0])
    return result


def get_list(sql):
    rows = q(sql, fetch="all") or []
    result = []
    for row in rows:
        result.append(row[0])
    return result


ID_FIELD_BY_TABLE = {
    "roles": "role_id",
    "units": "unit_id",
    "suppliers": "supplier_id",
    "manufacturers": "manufacturer_id",
    "categories": "category_id",
    "pickup_points": "pickup_point_id",
    "statuses": "status_id",
}


def get_or_create(cursor, table_name, name_field, value, default=None):
    if value is None or not str(value).strip():
        return default

    value = str(value).strip()
    id_field = ID_FIELD_BY_TABLE.get(table_name)

    cursor.execute(f"SELECT {id_field} FROM {table_name} WHERE {name_field} = %s", (value,))
    row = cursor.fetchone()
    if row:
        return row[0]

    cursor.execute(
        f"INSERT INTO {table_name} ({name_field}) VALUES (%s) RETURNING {id_field}",
        (value,),
    )
    return cursor.fetchone()[0]


def _with_cursor(connection, func, *args):
    cur = connection.cursor()
    result = func(cur, *args)
    cur.close()
    return result


PRODUCT_SELECT = (
    "SELECT p.product_id, p.article, p.product_name, c.category_name, p.description, "
    "m.manufacturer_name, s.supplier_name, p.price, u.unit_name, p.stock_quantity, p.discount, p.photo "
    "FROM products p "
    "LEFT JOIN categories c ON p.category_id = c.category_id "
    "LEFT JOIN manufacturers m ON p.manufacturer_id = m.manufacturer_id "
    "LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id "
    "LEFT JOIN units u ON p.unit_id = u.unit_id"
)


def auth_user(login, password):
    login, password = (login or "").strip(), (password or "").strip()
    row = q(
        "SELECT u.user_id, u.login, u.full_name, r.role_name "
        "FROM users u JOIN roles r ON u.role_id = r.role_id "
        "WHERE TRIM(u.login) = %s AND TRIM(u.user_password) = %s",
        params=(login, password),
        fetch="one",
        dict_cursor=True,
    )
    if row:
        row["id"] = row["user_id"]
    return row


def get_products_all(search_text="", supplier_name=None, order_by_quantity=None):
    query = PRODUCT_SELECT + " WHERE 1=1"
    params = []
    if search_text and search_text.strip():
        query_value = "%" + search_text.strip() + "%"
        query += (
            " AND (p.article ILIKE %s OR p.product_name ILIKE %s OR p.description ILIKE %s OR "
            "c.category_name ILIKE %s OR m.manufacturer_name ILIKE %s OR s.supplier_name ILIKE %s OR u.unit_name ILIKE %s)"
        )
        params = [query_value] * 7
    if supplier_name:
        query += " AND s.supplier_name = %s"
        params.append(supplier_name)
    if order_by_quantity == "asc":
        query += " ORDER BY p.stock_quantity ASC"
    elif order_by_quantity == "desc":
        query += " ORDER BY p.stock_quantity DESC"
    else:
        query += " ORDER BY p.product_id"
    return q(query, params=params, fetch="all", dict_cursor=True) or []


def get_product_by_id(product_id):
    return q(PRODUCT_SELECT + " WHERE p.product_id = %s", params=(product_id,), fetch="one", dict_cursor=True)


def get_product_id_by_article(article):
    """Точное совпадение артикула (после strip) с полем products.article."""
    article = (article or "").strip()
    if not article:
        return None
    row = q("SELECT product_id FROM products WHERE TRIM(article) = %s", params=(article,), fetch="one")
    return row[0] if row else None


def get_supplier_names():
    return _fetch_column("SELECT supplier_name FROM suppliers")


def get_category_names():
    return _fetch_column("SELECT category_name FROM categories")


def get_manufacturer_names():
    return _fetch_column("SELECT manufacturer_name FROM manufacturers")


def _get_or_create_supplier_id(cursor, supplier_name):
    return get_or_create(cursor, "suppliers", "supplier_name", supplier_name, default=None)


def _get_or_create_manufacturer_id(cursor, manufacturer_name):
    return get_or_create(cursor, "manufacturers", "manufacturer_name", manufacturer_name, default=None)


def _get_or_create_category_id(cursor, category_name):
    return get_or_create(cursor, "categories", "category_name", category_name, default=None)


def _get_or_create_unit_id(cursor, unit_name):
    return get_or_create(cursor, "units", "unit_name", unit_name, default=None)


def product_in_orders(product_id):
    return q("SELECT 1 FROM order_items WHERE product_id = %s LIMIT 1", params=(product_id,), fetch="one") is not None


def insert_product(data):
    article = (data.get("article") or "").strip() or "TMP"
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
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
            return pid


def update_product(product_id, data):
    article = (data.get("article") or "").strip() or ("ART-" + str(product_id))
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
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


def delete_product(product_id):
    q("DELETE FROM products WHERE product_id = %s", params=(product_id,))


def _get_or_create_status_id(cursor, status_name):
    return get_or_create(cursor, "statuses", "status_name", status_name or "новый", default=None)


def _get_or_create_pickup_point_id(cursor, pickup_address):
    return get_or_create(cursor, "pickup_points", "pickup_address", pickup_address, default=None)


def get_orders_all():
    rows = q(
        "SELECT o.order_id AS id, o.order_date, o.delivery_date, "
        "pp.pickup_address AS pickup_point_address, "
        "o.pickup_code AS pickup_code, "
        "st.status_name, "
        "o.user_id, u.full_name AS user_name "
        "FROM orders o JOIN users u ON o.user_id = u.user_id "
        "LEFT JOIN statuses st ON o.status_id = st.status_id "
        "LEFT JOIN pickup_points pp ON o.pickup_point_id = pp.pickup_point_id "
        "ORDER BY o.order_date DESC, o.order_id DESC",
        fetch="all",
        dict_cursor=True,
    ) or []
    return rows


def get_order_by_id(order_id):
    row = q(
        "SELECT o.order_id AS id, o.order_date, o.delivery_date, "
        "pp.pickup_address AS pickup_point_address, "
        "o.pickup_code AS pickup_code, "
        "st.status_name, o.user_id "
        "FROM orders o "
        "LEFT JOIN statuses st ON o.status_id = st.status_id "
        "LEFT JOIN pickup_points pp ON o.pickup_point_id = pp.pickup_point_id "
        "WHERE o.order_id = %s",
        params=(order_id,),
        fetch="one",
        dict_cursor=True,
    )
    return row


def get_users_list():
    return q("SELECT user_id, full_name FROM users", fetch="all", dict_cursor=True) or []


def get_order_statuses():
    return _fetch_column("SELECT status_name FROM statuses")


def get_pickup_addresses():
    return _fetch_column("SELECT pickup_address FROM pickup_points")


def insert_order(data):
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO orders (order_date, delivery_date, pickup_point_id, user_id, pickup_code, status_id) "
                "VALUES (%s, %s, %s, %s, %s, %s) RETURNING order_id",
                (
                    data.get("order_date"),
                    data.get("delivery_date"),
                    _get_or_create_pickup_point_id(cur, data.get("pickup_point")),
                    data.get("user_id"),
                    data.get("pickup_code"),
                    _get_or_create_status_id(cur, data.get("status")),
                ),
            )
            return cur.fetchone()[0]


def update_order(order_id, data):
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE orders SET order_date=%s, delivery_date=%s, pickup_point_id=%s, user_id=%s, pickup_code=%s, status_id=%s WHERE order_id=%s",
                (
                    data.get("order_date"),
                    data.get("delivery_date"),
                    _get_or_create_pickup_point_id(cur, data.get("pickup_point")),
                    data.get("user_id"),
                    data.get("pickup_code"),
                    _get_or_create_status_id(cur, data.get("status")),
                    order_id,
                ),
            )


def save_order_with_items(order_id, data, items):
    """
    Сохраняет шапку заказа и полностью заменяет строки order_items (транзакция).
    order_id=None — создание нового заказа.
    items: [{"product_id": int, "quantity": int}, ...]
    """
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            if order_id is None:
                cur.execute(
                    "INSERT INTO orders (order_date, delivery_date, pickup_point_id, user_id, pickup_code, status_id) "
                    "VALUES (%s, %s, %s, %s, %s, %s) RETURNING order_id",
                    (
                        data.get("order_date"),
                        data.get("delivery_date"),
                        _get_or_create_pickup_point_id(cur, data.get("pickup_point")),
                        data.get("user_id"),
                        data.get("pickup_code"),
                        _get_or_create_status_id(cur, data.get("status")),
                    ),
                )
                order_id = cur.fetchone()[0]
            else:
                cur.execute(
                    "UPDATE orders SET order_date=%s, delivery_date=%s, pickup_point_id=%s, user_id=%s, pickup_code=%s, status_id=%s WHERE order_id=%s",
                    (
                        data.get("order_date"),
                        data.get("delivery_date"),
                        _get_or_create_pickup_point_id(cur, data.get("pickup_point")),
                        data.get("user_id"),
                        data.get("pickup_code"),
                        _get_or_create_status_id(cur, data.get("status")),
                        order_id,
                    ),
                )
            cur.execute("DELETE FROM order_items WHERE order_id = %s", (order_id,))
            for it in items:
                cur.execute(
                    "INSERT INTO order_items (order_id, product_id, quantity) VALUES (%s, %s, %s)",
                    (order_id, it["product_id"], it["quantity"]),
                )


def delete_order(order_id):
    q("DELETE FROM orders WHERE order_id = %s", params=(order_id,))


def get_or_create_role_id(connection, role_name):
    if not role_name or not str(role_name).strip():
        return None
    role_name = str(role_name).strip()
    cur = connection.cursor()
    cur.execute("SELECT role_id FROM roles WHERE role_name = %s", (role_name,))
    row = cur.fetchone()
    if not row:
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
    if not items:
        return
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            for it in items:
                cur.execute(
                    "INSERT INTO order_items (order_id, product_id, quantity) VALUES (%s, %s, %s)",
                    (order_id, it["product_id"], it["quantity"]),
                )
