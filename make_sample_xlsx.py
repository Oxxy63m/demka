"""
Создаёт пример data.xlsx с листами и заголовками столбцов.
Заполните данные и запустите: python import_to_db.py (xlsx в папке import/)
"""
import os
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(ROOT, "data.xlsx")

users = pd.DataFrame(columns=["full_name", "login", "user_password", "role"])
products = pd.DataFrame(columns=[
    "article", "product_name", "unit", "price", "supplier", "manufacturer",
    "category", "discount", "stock_quantity", "description", "photo"
])
orders = pd.DataFrame(columns=[
    "order_date", "delivery_date", "pickup_point", "user_id", "pickup_code", "status"
])
order_items = pd.DataFrame(columns=["order_id", "product_id", "quantity"])

# Пример одной строки в каждом листе (можно удалить или изменить)
users.loc[0] = ["Иванов И.И.", "admin", "123", "administrator"]
products.loc[0] = ["ART-001", "Кроссовки", "шт.", 3500.00, "Поставщик 1", "Nike", "Обувь", 10, 50, "Описание", None]
orders.loc[0] = ["2024-01-15", "2024-01-20", "ул. Примерная, 1", 1, 12345, "Доставлен"]
order_items.loc[0] = [1, 1, 2]

with pd.ExcelWriter(PATH, engine="openpyxl") as w:
    users.to_excel(w, sheet_name="users", index=False)
    products.to_excel(w, sheet_name="products", index=False)
    orders.to_excel(w, sheet_name="orders", index=False)
    order_items.to_excel(w, sheet_name="order_items", index=False)

print("Создан файл:", PATH)
