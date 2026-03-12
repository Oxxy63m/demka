# Настройки приложения: папка ресурсов относительно проекта, пути к интерфейсам, параметры БД.
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Все ресурсы (иконки, плейсхолдер, фото товаров, Excel для импорта) — в папке resources в проекте.
DATA_DIR = os.path.join(ROOT, "resources")
APP_ICON = os.path.join(DATA_DIR, "icon.ico")
LOGIN_LOGO = os.path.join(DATA_DIR, "icon.png")

UI = {
    "login": os.path.join(ROOT, "ui", "login.ui"),
    "main": os.path.join(ROOT, "ui", "main.ui"),
    "orders": os.path.join(ROOT, "ui", "orders_list.ui"),
    "order": os.path.join(ROOT, "ui", "order_form.ui"),
    "prod": os.path.join(ROOT, "ui", "product_form.ui"),
    "card": os.path.join(ROOT, "ui", "product_item.ui"),
    "cart": os.path.join(ROOT, "ui", "cart.ui"),
}

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", "5432")),
    "database": os.environ.get("DB_NAME", "demka"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", "1234"),
}

IMAGES_FOLDER = "product_images"
IMAGE_MAX_WIDTH = 300
IMAGE_MAX_HEIGHT = 200
PLACEHOLDER_IMAGE = "picture.png"

ROLE_GUEST = "guest"
ROLE_CLIENT = "client"
ROLE_MANAGER = "manager"
ROLE_ADMINISTRATOR = "administrator"
