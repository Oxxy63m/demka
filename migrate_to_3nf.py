# Миграция существующей БД к третьей нормальной форме (3НФ).
# Запуск: python migrate_to_3nf.py
# Выполняет один раз: создаёт справочники, переносит данные, переводит таблицы на FK.

import os
import sys
import psycopg2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from App.config import DB_CONFIG


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    cur = conn.cursor()
    try:
        # Проверяем: уже 3НФ? (у users есть role_id)
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'users' AND column_name = 'role_id'
        """)
        if cur.fetchone():
            print("БД уже в 3НФ (users.role_id есть). Миграция не требуется.")
            return

        # 1) Создать справочники
        cur.execute("CREATE TABLE IF NOT EXISTS roles (role_id SERIAL PRIMARY KEY, name VARCHAR(100) NOT NULL UNIQUE)")
        cur.execute("CREATE TABLE IF NOT EXISTS suppliers (supplier_id SERIAL PRIMARY KEY, name VARCHAR(255) NOT NULL)")
        cur.execute("CREATE TABLE IF NOT EXISTS manufacturers (manufacturer_id SERIAL PRIMARY KEY, name VARCHAR(255) NOT NULL)")
        cur.execute("CREATE TABLE IF NOT EXISTS categories (category_id SERIAL PRIMARY KEY, name VARCHAR(255) NOT NULL)")
        cur.execute("CREATE TABLE IF NOT EXISTS order_statuses (status_id SERIAL PRIMARY KEY, name VARCHAR(100) NOT NULL UNIQUE)")
        cur.execute("CREATE TABLE IF NOT EXISTS pickup_points (pickup_point_id SERIAL PRIMARY KEY, address VARCHAR(500) NOT NULL)")

        # 2) Заполнить справочники из существующих данных
        cur.execute("INSERT INTO roles (name) SELECT DISTINCT role FROM users WHERE role IS NOT NULL ON CONFLICT (name) DO NOTHING")
        cur.execute("INSERT INTO suppliers (name) SELECT DISTINCT supplier FROM products WHERE supplier IS NOT NULL AND supplier != '' AND NOT EXISTS (SELECT 1 FROM suppliers)")
        cur.execute("INSERT INTO manufacturers (name) SELECT DISTINCT manufacturer FROM products WHERE manufacturer IS NOT NULL AND manufacturer != '' AND NOT EXISTS (SELECT 1 FROM manufacturers)")
        cur.execute("INSERT INTO categories (name) SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND category != '' AND NOT EXISTS (SELECT 1 FROM categories)")
        cur.execute("INSERT INTO order_statuses (name) SELECT DISTINCT status FROM orders WHERE status IS NOT NULL ON CONFLICT (name) DO NOTHING")
        cur.execute("INSERT INTO pickup_points (address) SELECT DISTINCT pickup_point FROM orders WHERE pickup_point IS NOT NULL AND pickup_point != '' AND NOT EXISTS (SELECT 1 FROM pickup_points)")

        # Добавить стандартные роли/статусы, если их не было в данных
        for name in ('guest', 'client', 'manager', 'administrator'):
            cur.execute("INSERT INTO roles (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (name,))
        for name in ('новый', 'в обработке', 'доставляется', 'выполнен', 'отменён'):
            cur.execute("INSERT INTO order_statuses (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (name,))

        # 3) Добавить новые столбцы
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS role_id INTEGER REFERENCES roles(role_id)")
        cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS supplier_id INTEGER REFERENCES suppliers(supplier_id)")
        cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS manufacturer_id INTEGER REFERENCES manufacturers(manufacturer_id)")
        cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS category_id INTEGER REFERENCES categories(category_id)")
        cur.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS pickup_point_id INTEGER REFERENCES pickup_points(pickup_point_id)")
        cur.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS status_id INTEGER REFERENCES order_statuses(status_id)")

        # 4) Заполнить новые столбцы
        cur.execute("UPDATE users u SET role_id = r.role_id FROM roles r WHERE r.name = u.role AND u.role_id IS NULL")
        cur.execute("UPDATE products p SET supplier_id = s.supplier_id FROM suppliers s WHERE s.name = p.supplier AND p.supplier_id IS NULL")
        cur.execute("UPDATE products p SET manufacturer_id = m.manufacturer_id FROM manufacturers m WHERE m.name = p.manufacturer AND p.manufacturer_id IS NULL")
        cur.execute("UPDATE products p SET category_id = c.category_id FROM categories c WHERE c.name = p.category AND p.category_id IS NULL")
        cur.execute("UPDATE orders o SET pickup_point_id = pp.pickup_point_id FROM pickup_points pp WHERE pp.address = o.pickup_point AND o.pickup_point_id IS NULL")
        cur.execute("UPDATE orders o SET status_id = st.status_id FROM order_statuses st WHERE st.name = o.status AND o.status_id IS NULL")

        # Для строк без соответствия в справочнике — подставить первый доступный
        cur.execute("UPDATE users SET role_id = (SELECT role_id FROM roles LIMIT 1) WHERE role_id IS NULL")
        cur.execute("UPDATE orders SET status_id = (SELECT status_id FROM order_statuses WHERE name = 'новый' LIMIT 1) WHERE status_id IS NULL")

        # 5) Удалить старые столбцы и сделать новые NOT NULL где нужно
        cur.execute("ALTER TABLE users DROP COLUMN IF EXISTS role")
        cur.execute("ALTER TABLE users ALTER COLUMN role_id SET NOT NULL")
        cur.execute("ALTER TABLE products DROP COLUMN IF EXISTS supplier")
        cur.execute("ALTER TABLE products DROP COLUMN IF EXISTS manufacturer")
        cur.execute("ALTER TABLE products DROP COLUMN IF EXISTS category")
        cur.execute("ALTER TABLE orders DROP COLUMN IF EXISTS pickup_point")
        cur.execute("ALTER TABLE orders DROP COLUMN IF EXISTS status")

        conn.commit()
        print("Миграция в 3НФ выполнена успешно.")
    except Exception as e:
        conn.rollback()
        print("Ошибка миграции:", e)
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
