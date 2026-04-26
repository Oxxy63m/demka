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
    "SELECT p.product_id, p.product_art AS article, p.product_name, "
    "c.categ_name AS category_name, p.product_desc AS description, "
    "p.product_manufac AS manufacturer_name, s.supp_name AS supplier_name, "
    "p.product_price AS price, p.product_unit AS unit_name, "
    "p.product_stock AS stock_quantity, p.product_discount AS discount, "
    "p.product_photo AS photo "
    "FROM products p "
    "LEFT JOIN categories c ON p.categ_id = c.categ_id "
    "LEFT JOIN suppliers s ON p.supp_id = s.supp_id"
)


def auth_user(login, password):
    row = q(
        "SELECT u.user_id, u.user_login AS login, u.user_name AS full_name, u.user_role AS role_name "
        "FROM users u WHERE TRIM(u.user_login)=%s AND TRIM(u.user_password)=%s",
        (login.strip(), password.strip()),
        fetch="one",
        d=True,
    )
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
    return _names("SELECT supp_name FROM suppliers ORDER BY supp_name")


def get_category_names():
    return _names("SELECT categ_name FROM categories ORDER BY categ_name")


def get_manufacturer_names():
    return _names(
        "SELECT DISTINCT TRIM(product_manufac) FROM products "
        "WHERE product_manufac IS NOT NULL AND TRIM(product_manufac) <> '' "
        "ORDER BY TRIM(product_manufac)"
    )


def _fk(table, id_col, name_col, name):
    name = (name or "").strip()
    if not name:
        return None
    r = q(f"SELECT {id_col} FROM {table} WHERE {name_col}=%s", (name,), fetch="one")
    return r[0] if r else None


def _vals(data):
    ph = data.get("photo")
    if ph is not None and not isinstance(ph, str):
        ph = str(ph).strip() or None
    elif isinstance(ph, str):
        ph = ph.strip() or None
    return (
        data.get("product_name"),
        (data.get("unit") or "").strip() or None,
        data.get("price"),
        _fk("suppliers", "supp_id", "supp_name", data.get("supplier")),
        (data.get("manufacturer") or "").strip() or None,
        _fk("categories", "categ_id", "categ_name", data.get("category")),
        int(float(data.get("discount") or 0)),
        int(float(data.get("stock_quantity") or 0)),
        data.get("description"),
        ph,
    )


def insert_product(data):
    art = data["article"].strip()
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO products (product_art, product_name, product_unit, product_price, supp_id, "
                "product_manufac, categ_id, product_discount, product_stock, product_desc, product_photo) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING product_id",
                (art,) + _vals(data),
            )
            return cur.fetchone()[0]


def update_product(product_id, data):
    art = data["article"].strip()
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE products SET product_art=%s, product_name=%s, product_unit=%s, product_price=%s, supp_id=%s, "
                "product_manufac=%s, categ_id=%s, product_discount=%s, product_stock=%s, product_desc=%s, product_photo=%s "
                "WHERE product_id=%s",
                (art,) + _vals(data) + (product_id,),
            )


def delete_product(product_id):
    q("DELETE FROM products WHERE product_id=%s", (product_id,))


def parse_order_line_items(text):
    """Формат как в Excel: артикул, количество, артикул, количество… Количество можно опустить (=1)."""
    raw = (text or "").replace("\n", ",").replace(";", ",")
    parts = [p.strip() for p in raw.split(",")]
    parts = [p for p in parts if p]
    items = []
    i = 0
    while i < len(parts):
        art = parts[i]
        i += 1
        qty = 1
        if i < len(parts):
            maybe = parts[i].replace(" ", "").replace("\u00a0", "")
            if maybe.isdigit() and int(maybe) > 0:
                qty = int(maybe)
                i += 1
        items.append((art, qty))
    return items


def _order_items_for_save(product_article_text):
    lines = parse_order_line_items(product_article_text)
    if not lines:
        raise ValueError("Укажите хотя бы одну позицию: артикул или «артикул, количество» через запятую.")
    rows = []
    for art, qty in lines:
        r = q(
            "SELECT product_id FROM products WHERE TRIM(product_art)=%s",
            (art.strip(),),
            fetch="one",
        )
        if not r:
            raise ValueError(f"Товар с артикулом «{art}» не найден.")
        rows.append((r[0], qty))
    return rows


def format_order_items_line(items):
    """Список dict с article, quantity → строка для поля ввода."""
    if not items:
        return ""
    parts = []
    for it in items:
        a = (it.get("article") or "").strip()
        qv = int(it.get("quantity") or 1)
        if not a:
            continue
        parts.append(f"{a}, {qv}" if qv != 1 else a)
    return ", ".join(parts)


def get_orders_all():
    return q(
        "SELECT o.order_id AS id, o.order_date, o.order_pup_date AS delivery_date, "
        "pp.pp_name AS pickup_point_address, "
        "COALESCE("
        "(SELECT STRING_AGG("
        "p.product_art || CASE WHEN oi.product_quantity > 1 THEN ' ×' || oi.product_quantity::text ELSE '' END, "
        "', ' ORDER BY oi.order_item_id) "
        "FROM order_items oi JOIN products p ON p.product_id = oi.product_id "
        "WHERE oi.order_id = o.order_id), '') AS article, st.status_name "
        "FROM orders o "
        "LEFT JOIN statuses st ON o.status_id = st.status_id "
        "LEFT JOIN pickup_points pp ON o.pp_id = pp.pp_id "
        "ORDER BY o.order_date DESC, o.order_id DESC",
        fetch="all",
        d=True,
    )


def get_order_by_id(order_id):
    row = q(
        "SELECT o.order_id AS id, o.order_date, o.order_pup_date AS delivery_date, "
        "pp.pp_name AS pickup_point_address, "
        "o.order_pp_code AS receiver_code, o.user_name AS client_name, "
        "st.status_name, o.pp_id AS pickup_point_id "
        "FROM orders o "
        "LEFT JOIN statuses st ON o.status_id = st.status_id "
        "LEFT JOIN pickup_points pp ON o.pp_id = pp.pp_id "
        "WHERE o.order_id=%s",
        (order_id,),
        fetch="one",
        d=True,
    )
    if not row:
        return None
    row["items"] = q(
        "SELECT oi.product_id, p.product_art AS article, oi.product_quantity AS quantity FROM order_items oi "
        "JOIN products p ON p.product_id = oi.product_id WHERE oi.order_id=%s "
        "ORDER BY oi.order_item_id",
        (order_id,),
        fetch="all",
        d=True,
    )
    return row


def get_order_statuses():
    return _names("SELECT status_name FROM statuses ORDER BY status_name")


def get_pickup_points():
    return q(
        "SELECT pp_id AS pickup_point_id, pp_name AS pickup_address FROM pickup_points ORDER BY pp_id",
        fetch="all",
        d=True,
    )


def save_order(order_id, data):
    t = (data.get("product_article") or "").strip()
    item_rows = _order_items_for_save(t)
    status_id = _fk("statuses", "status_id", "status_name", data["status_name"])
    ppid = data.get("pickup_point_id")
    rc = data.get("receiver_code")
    rc = None if rc is None else str(rc).strip() or None
    try:
        rc_num = int(rc) if rc is not None and rc != "" else None
    except ValueError:
        rc_num = None
    client_name = (data.get("user_name") or "").strip() or None
    head = (
        data["order_date"],
        data["delivery_date"],
        ppid,
        client_name,
        status_id,
        rc_num,
    )
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            if order_id is None:
                cur.execute(
                    "INSERT INTO orders (order_date, order_pup_date, pp_id, user_name, "
                    "status_id, order_pp_code) VALUES (%s,%s,%s,%s,%s,%s) RETURNING order_id",
                    head,
                )
                oid = cur.fetchone()[0]
            else:
                cur.execute(
                    "UPDATE orders SET order_date=%s, order_pup_date=%s, pp_id=%s, user_name=%s, "
                    "status_id=%s, order_pp_code=%s WHERE order_id=%s",
                    head + (order_id,),
                )
                oid = order_id
                cur.execute("DELETE FROM order_items WHERE order_id=%s", (oid,))
            for product_id, qty in item_rows:
                cur.execute(
                    "INSERT INTO order_items (order_id, product_id, product_quantity) VALUES (%s,%s,%s)",
                    (oid, product_id, qty),
                )
            return oid


def delete_order(order_id):
    q("DELETE FROM orders WHERE order_id=%s", (order_id,))
