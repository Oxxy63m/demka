# Настройки приложения: папки с данными, пути к интерфейсам, параметры БД. Менять DATA_DIR и DB_CONFIG под свой компьютер.
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.normpath(os.path.abspath(os.environ.get("DATA_DIR", r"C:\Users\user\Documents\fuckdemoexam\Модуль 1\import")))
PHOTOS_DIR = DATA_DIR
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

RESOURCES_DIR = os.path.join(ROOT, "resources")
IMAGES_FOLDER = "product_images"
IMAGE_MAX_WIDTH = 300
IMAGE_MAX_HEIGHT = 200
PLACEHOLDER_IMAGE = "picture.png"

ROLE_GUEST = "guest"
ROLE_CLIENT = "client"
ROLE_MANAGER = "manager"
ROLE_ADMINISTRATOR = "administrator"
ORDER_STATUSES = ["новый", "в обработке", "доставляется", "выполнен", "отменён"]
PICKUP_POINTS = ["Пункт выдачи 1", "Пункт выдачи 2", "Пункт выдачи 3"]
