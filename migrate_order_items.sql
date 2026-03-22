-- Переход с orders.product_id на order_items (одна строка заказа → несколько товаров).
-- Выполни один раз в существующей БД. Для новой установки достаточно DB.sql.

BEGIN;

CREATE TABLE IF NOT EXISTS order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(product_id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0)
);

-- Если колонка product_id ещё есть — переносим в позиции
INSERT INTO order_items (order_id, product_id, quantity)
SELECT order_id, product_id, 1
FROM orders
WHERE product_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM order_items oi WHERE oi.order_id = orders.order_id
  );

ALTER TABLE orders DROP COLUMN IF EXISTS product_id;

-- Состав заказа только в order_items; дублирующий текст не храним
ALTER TABLE orders DROP COLUMN IF EXISTS order_article_text;

COMMIT;
