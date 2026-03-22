-- Удалить устаревшую колонку (состав заказа — в order_items).
ALTER TABLE orders DROP COLUMN IF EXISTS order_article_text;
