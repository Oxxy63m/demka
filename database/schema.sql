-- Схема по ERD: 4 таблицы (users, products, orders, order_items)

-- 1) Пользователи
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    login VARCHAR(255) NOT NULL UNIQUE,
    user_password VARCHAR(255) NOT NULL,
    role VARCHAR(100) NOT NULL
);

-- 2) Товары
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    article VARCHAR(50),
    product_name VARCHAR(255) NOT NULL,
    unit VARCHAR(20),
    price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    supplier VARCHAR(50),
    manufacturer VARCHAR(50),
    category VARCHAR(50),
    discount NUMERIC(5, 2) DEFAULT 0 CHECK (discount >= 0 AND discount <= 100),
    stock_quantity INTEGER NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    description TEXT,
    photo VARCHAR(255)
);

-- 3) Заказы (адрес пункта выдачи хранится в pickup_point)
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    order_date DATE NOT NULL,
    delivery_date DATE,
    pickup_point VARCHAR(500),
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
    pickup_code INTEGER,
    status VARCHAR(50)
);

-- 4) Позиции заказа (связь заказ — товар — количество)
CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL CHECK (quantity > 0)
);
