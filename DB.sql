-- Схема БД в третьей нормальной форме (3НФ), исправленная по замечаниям
-- Без order_article в orders (вычисляется из order_items + products)
-- unit_price в order_items (историчность), UNIQUE(order_id, product_id)
-- units справочник, article NOT NULL UNIQUE

-- Справочники
CREATE TABLE roles (
    role_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE suppliers (
    supplier_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE manufacturers (
    manufacturer_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE units (
    unit_id SERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE order_statuses (
    status_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE pickup_points (
    pickup_point_id SERIAL PRIMARY KEY,
    address VARCHAR(500) NOT NULL
);

-- Пользователи
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    login VARCHAR(255) NOT NULL UNIQUE,
    user_password VARCHAR(255) NOT NULL,
    role_id INTEGER NOT NULL REFERENCES roles(role_id) ON DELETE RESTRICT
);

-- Товары: article уникален и NOT NULL, unit_id FK
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    article VARCHAR(50) NOT NULL UNIQUE,
    product_name VARCHAR(255) NOT NULL,
    unit_id INTEGER REFERENCES units(unit_id) ON DELETE SET NULL,
    price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    supplier_id INTEGER REFERENCES suppliers(supplier_id) ON DELETE SET NULL,
    manufacturer_id INTEGER REFERENCES manufacturers(manufacturer_id) ON DELETE SET NULL,
    category_id INTEGER REFERENCES categories(category_id) ON DELETE SET NULL,
    discount NUMERIC(5, 2) DEFAULT 0 CHECK (discount >= 0 AND discount <= 100),
    stock_quantity INTEGER NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    description TEXT,
    photo VARCHAR(255)
);

-- Заказы: без order_article (данные о товарах только в order_items)
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    order_date DATE NOT NULL DEFAULT CURRENT_DATE,
    delivery_date DATE,
    pickup_point_id INTEGER REFERENCES pickup_points(pickup_point_id) ON DELETE SET NULL,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
    pickup_code VARCHAR(50),
    status_id INTEGER REFERENCES order_statuses(status_id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Позиции заказа: unit_price — цена в момент заказа (историчность), UNIQUE(order_id, product_id)
CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0),
    CONSTRAINT uq_order_product UNIQUE (order_id, product_id)
);

-- Начальные данные
INSERT INTO roles (name) VALUES ('guest'), ('client'), ('manager'), ('administrator');
INSERT INTO order_statuses (name) VALUES ('новый'), ('в обработке'), ('доставляется'), ('выполнен'), ('отменён');
INSERT INTO units (code, name) VALUES ('шт', 'Штуки'), ('кг', 'Килограммы'), ('уп', 'Упаковка');

-- TRUNCATE users, products, orders, order_items RESTART IDENTITY CASCADE;
