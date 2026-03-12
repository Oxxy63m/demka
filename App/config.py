# Настройки приложения. Запуск — из корня проекта (main.py). ui/ и resources/ — относительно корня.
DATA_DIR = "resources"
APP_ICON = "resources/icon.ico"
LOGIN_LOGO = "resources/icon.png"

UI = {
    "login": "ui/login.ui",
    "main": "ui/main.ui",
    "orders": "ui/orders_list.ui",
    "order": "ui/order_form.ui",
    "prod": "ui/product_form.ui",
    "card": "ui/product_item.ui",
    "cart": "ui/cart.ui",
}

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "demka",
    "user": "postgres",
    "password": "1234",
}

IMAGES_FOLDER = "product_images"
IMAGE_MAX_WIDTH = 300
IMAGE_MAX_HEIGHT = 200
PLACEHOLDER_IMAGE = "picture.png"

ROLE_GUEST = "guest"
ROLE_CLIENT = "client"
ROLE_MANAGER = "manager"
ROLE_ADMINISTRATOR = "administrator"
