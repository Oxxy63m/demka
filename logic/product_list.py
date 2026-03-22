# product_list.py
from App.db import delete_product, get_products_all, get_supplier_names

load_products = get_products_all
__all__ = ["delete_product", "get_products_all", "get_supplier_names", "load_products"]
