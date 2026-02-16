import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import psycopg2
from psycopg2.extras import RealDictCursor
from config import DB_CONFIG


def auth_user(login, password):
    login = (login or "").strip()
    password = (password or "").strip()
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT user_id, login, full_name, role FROM users WHERE TRIM(login) = %s AND TRIM(user_password) = %s", (login, password))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        row["id"] = row["user_id"]
    return row


def get_products_all(search_text="", supplier_name=None, order_by_quantity=None):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    query = "SELECT id, article, product_name, category, description, manufacturer, supplier, price, unit, stock_quantity, discount, photo FROM products WHERE 1=1"
    params = []
    if search_text and search_text.strip():
        pattern = "%" + search_text.strip() + "%"
        query += " AND (article ILIKE %s OR product_name ILIKE %s OR description ILIKE %s OR category ILIKE %s OR manufacturer ILIKE %s OR supplier ILIKE %s OR unit ILIKE %s)"
        params = [pattern, pattern, pattern, pattern, pattern, pattern, pattern]
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
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id, article, product_name, category, description, manufacturer, supplier, price, unit, stock_quantity, discount, photo FROM products WHERE id = %s", (product_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def get_supplier_names():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT supplier FROM products WHERE supplier IS NOT NULL AND supplier != '' ORDER BY supplier")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [row[0] for row in rows]


def product_in_orders(product_id):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM order_items WHERE product_id = %s LIMIT 1", (product_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row is not None


def insert_product(data):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO products (article, product_name, unit, price, supplier, manufacturer, category, discount, stock_quantity, description, photo) VALUES (%(article)s, %(product_name)s, %(unit)s, %(price)s, %(supplier)s, %(manufacturer)s, %(category)s, %(discount)s, %(stock_quantity)s, %(description)s, %(photo)s) RETURNING id",
        data,
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return new_id


def update_product(product_id, data):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    data["id"] = product_id
    cur.execute(
        "UPDATE products SET article=%(article)s, product_name=%(product_name)s, category=%(category)s, description=%(description)s, manufacturer=%(manufacturer)s, supplier=%(supplier)s, price=%(price)s, unit=%(unit)s, stock_quantity=%(stock_quantity)s, discount=%(discount)s, photo=%(photo)s WHERE id=%(id)s",
        data,
    )
    conn.commit()
    cur.close()
    conn.close()


def delete_product(product_id):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
    conn.commit()
    cur.close()
    conn.close()
