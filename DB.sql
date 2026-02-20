-- Схема БД в третьей нормальной форме (3НФ)
-- Справочники: roles, suppliers, manufacturers, categories, order_statuses, pickup_points
-- Основные: users, products, orders, order_items

-- Справочник ролей (устраняет повторение role в users)
CREATE TABLE roles (
    role_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

-- Справочник поставщиков (устраняет повторение supplier в products)
CREATE TABLE suppliers (
    supplier_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

-- Справочник производителей
CREATE TABLE manufacturers (
    manufacturer_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

-- Справочник категорий
CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

-- Справочник статусов заказа
CREATE TABLE order_statuses (
    status_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

-- Справочник пунктов выдачи
CREATE TABLE pickup_points (
    pickup_point_id SERIAL PRIMARY KEY,
    address VARCHAR(500) NOT NULL
);

-- Пользователи: роль по FK (3НФ)
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    login VARCHAR(255) NOT NULL UNIQUE,
    user_password VARCHAR(255) NOT NULL,
    role_id INTEGER NOT NULL REFERENCES roles(role_id) ON DELETE RESTRICT
);

-- Товары: поставщик, производитель, категория по FK (3НФ)
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    article VARCHAR(50),
    product_name VARCHAR(255) NOT NULL,
    unit VARCHAR(20),
    price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    supplier_id INTEGER REFERENCES suppliers(supplier_id) ON DELETE SET NULL,
    manufacturer_id INTEGER REFERENCES manufacturers(manufacturer_id) ON DELETE SET NULL,
    category_id INTEGER REFERENCES categories(category_id) ON DELETE SET NULL,
    discount NUMERIC(5, 2) DEFAULT 0 CHECK (discount >= 0 AND discount <= 100),
    stock_quantity INTEGER NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    description TEXT,
    photo VARCHAR(255)
);

-- Заказы: статус и пункт выдачи по FK (3НФ)
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    order_article VARCHAR(500),
    order_date DATE NOT NULL,
    delivery_date DATE,
    pickup_point_id INTEGER REFERENCES pickup_points(pickup_point_id) ON DELETE SET NULL,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
    pickup_code INTEGER,
    status_id INTEGER REFERENCES order_statuses(status_id) ON DELETE SET NULL
);

-- Позиции заказа (артикул заказа вычисляется из order_items + products, без отдельной таблицы)
CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL CHECK (quantity > 0)
);

-- Начальные данные справочников (чтобы приложение работало сразу)
INSERT INTO roles (name) VALUES ('guest'), ('client'), ('manager'), ('administrator');
INSERT INTO order_statuses (name) VALUES ('новый'), ('в обработке'), ('доставляется'), ('выполнен'), ('отменён');

-- Если после многократного импорта сбилась нумерация id — выполни:
-- TRUNCATE users, products, orders, order_items RESTART IDENTITY CASCADE;
