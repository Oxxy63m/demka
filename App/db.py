# db.py
import psycopg2
from psycopg2.extras import RealDictCursor

from App.config import DB_CONFIG


def q(sql, params=(), fetch=None, d=False):
    cf = RealDictCursor if d else None
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor(cursor_factory=cf) as cur:
            cur.execute(sql, params)
            if fetch == "one":
                return cur.fetchone()
            if fetch == "all":
                return cur.fetchall()


def _names(sql):
    return [r[0] for r in q(sql, fetch="all")]


SQL_PRODUCTS = (
    "SELECT p.product_id, p.article, p.product_name, c.category_name, p.description, "
    "m.manufacturer_name, s.supplier_name, p.price, u.unit_name, p.stock_quantity, p.discount, p.photo "
    "FROM products p "
    "LEFT JOIN categories c ON p.category_id = c.category_id "
    "LEFT JOIN manufacturers m ON p.manufacturer_id = m.manufacturer_id "
    "LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id "
    "LEFT JOIN units u ON p.unit_id = u.unit_id"
)


def auth_user(login, password):
    row = q(
        "SELECT u.user_id, u.login, u.full_name, r.role_name FROM users u "
        "JOIN roles r ON u.role_id = r.role_id "
        "WHERE TRIM(u.login)=%s AND TRIM(u.user_password)=%s",
        (login.strip(), password.strip()),
        fetch="one",
        d=True,
    )
    if row:
        row["id"] = row["user_id"]
    return row


def get_products_all(search_text="", supplier_name=None, order_by_quantity=None):
    sql, params = SQL_PRODUCTS + " WHERE 1=1", []
    if search_text.strip():
        v = f"%{search_text.strip()}%"
        sql += (
            " AND (p.article ILIKE %s OR p.product_name ILIKE %s OR p.description ILIKE %s OR "
            "c.category_name ILIKE %s OR m.manufacturer_name ILIKE %s OR s.supplier_name ILIKE %s OR u.unit_name ILIKE %s)"
        )
        params = [v] * 7
    if supplier_name:
        sql += " AND s.supplier_name = %s"
        params.append(supplier_name)
    if order_by_quantity == "asc":
        sql += " ORDER BY p.stock_quantity ASC"
    elif order_by_quantity == "desc":
        sql += " ORDER BY p.stock_quantity DESC"
    else:
        sql += " ORDER BY p.product_id"
    return q(sql, params, fetch="all", d=True)


def get_product_by_id(product_id):
    return q(SQL_PRODUCTS + " WHERE p.product_id = %s", (product_id,), fetch="one", d=True)


def get_supplier_names():
    return _names("SELECT supplier_name FROM suppliers ORDER BY supplier_name")


def get_category_names():
    return _names("SELECT category_name FROM categories ORDER BY category_name")


def get_manufacturer_names():
    return _names("SELECT manufacturer_name FROM manufacturers ORDER BY manufacturer_name")


def _fk(table, id_col, name_col, name):
    name = (name or "").strip()
    if not name:
        return None
    r = q(f"SELECT {id_col} FROM {table} WHERE {name_col}=%s", (name,), fetch="one")
    return r[0]


def _vals(data):
    ph = data.get("photo")
    return (
        data.get("product_name"),
        _fk("units", "unit_id", "unit_name", data.get("unit")),
        data.get("price"),
        _fk("suppliers", "supplier_id", "supplier_name", data.get("supplier")),
        _fk("manufacturers", "manufacturer_id", "manufacturer_name", data.get("manufacturer")),
        _fk("categories", "category_id", "category_name", data.get("category")),
        data.get("discount"),
        data.get("stock_quantity"),
        data.get("description"),
        psycopg2.Binary(ph) if ph else None,
    )


def insert_product(data):
    art = data["article"].strip()
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO products (article, product_name, unit_id, price, supplier_id, manufacturer_id, "
                "category_id, discount, stock_quantity, description, photo) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING product_id",
                (art,) + _vals(data),
            )
            return cur.fetchone()[0]


def update_product(product_id, data):
    art = data["article"].strip()
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE products SET article=%s, product_name=%s, unit_id=%s, price=%s, supplier_id=%s, "
                "manufacturer_id=%s, category_id=%s, discount=%s, stock_quantity=%s, description=%s, photo=%s "
                "WHERE product_id=%s",
                (art,) + _vals(data) + (product_id,),
            )


def delete_product(product_id):
    q("DELETE FROM products WHERE product_id=%s", (product_id,))


def first_article_from_order_line(text):
    s = (text or "").strip()
    if not s:
        return None
    parts = [p.strip() for p in s.split(",") if p.strip()]
    return parts[0] if parts else None


def get_orders_all():
    return q(
        "SELECT o.order_id AS id, o.order_date, o.delivery_date, "
        "pp.pickup_address AS pickup_point_address, "
        "COALESCE(NULLIF(TRIM(o.order_article_text), ''), p.article) AS article, st.status_name "
        "FROM orders o JOIN products p ON o.product_id = p.product_id "
        "LEFT JOIN statuses st ON o.status_id = st.status_id "
        "LEFT JOIN pickup_points pp ON o.pickup_point_id = pp.pickup_point_id "
        "ORDER BY o.order_date DESC, o.order_id DESC",
        fetch="all",
        d=True,
    )


def get_order_by_id(order_id):
    return q(
        "SELECT o.order_id AS id, o.order_date, o.delivery_date, "
        "pp.pickup_address AS pickup_point_address, p.article AS product_article, "
        "o.order_article_text, o.receiver_code, o.user_id, u.full_name AS client_name, "
        "st.status_name, o.product_id, o.pickup_point_id "
        "FROM orders o JOIN products p ON o.product_id = p.product_id "
        "LEFT JOIN statuses st ON o.status_id = st.status_id "
        "LEFT JOIN pickup_points pp ON o.pickup_point_id = pp.pickup_point_id "
        "LEFT JOIN users u ON o.user_id = u.user_id WHERE o.order_id=%s",
        (order_id,),
        fetch="one",
        d=True,
    )


def get_order_statuses():
    return _names("SELECT status_name FROM statuses ORDER BY status_name")


def get_pickup_points():
    return q(
        "SELECT pickup_point_id, pickup_address FROM pickup_points ORDER BY pickup_point_id",
        fetch="all",
        d=True,
    )


def save_order(order_id, data):
    t = data["product_article"].strip()
    art = t.split(",")[0].strip()
    product_id = q("SELECT product_id FROM products WHERE TRIM(article)=%s", (art,), fetch="one")[0]
    status_id = _fk("statuses", "status_id", "status_name", data["status_name"])
    uid = data.get("user_id")
    pid = data.get("pickup_point_id")
    rc = data.get("receiver_code")
    rc = None if not rc else str(rc).strip() or None
    row = (
        data["order_date"],
        data["delivery_date"],
        pid,
        uid,
        product_id,
        status_id,
        t,
        rc,
    )
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            if order_id is None:
                cur.execute(
                    "INSERT INTO orders (order_date, delivery_date, pickup_point_id, user_id, product_id, "
                    "status_id, order_article_text, receiver_code) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING order_id",
                    row,
                )
                return cur.fetchone()[0]
            cur.execute(
                "UPDATE orders SET order_date=%s, delivery_date=%s, pickup_point_id=%s, user_id=%s, product_id=%s, "
                "status_id=%s, order_article_text=%s, receiver_code=%s WHERE order_id=%s",
                row + (order_id,),
            )
            return order_id


def delete_order(order_id):
    q("DELETE FROM orders WHERE order_id=%s", (order_id,))
