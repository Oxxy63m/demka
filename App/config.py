# App/config.py — настройки приложения и БД (где host, пароль, папка картинок, роли)
import os

# Корень проекта (для путей к UI)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Абсолютный путь к папке с Excel и фото (импорт и отображение картинок товаров)
DATA_DIR = os.environ.get("DATA_DIR", r"C:\Users\user\Documents\fuckdemoexam\Модуль 1")
# Пути к .ui файлам (только разметка в папке UI)
UI = {
    "login": os.path.join(ROOT, "UI", "login.ui"),
    "main": os.path.join(ROOT, "UI", "main.ui"),
    "orders": os.path.join(ROOT, "UI", "orders_list.ui"),
    "order": os.path.join(ROOT, "UI", "order_form.ui"),
    "prod": os.path.join(ROOT, "UI", "product_form.ui"),
    "card": os.path.join(ROOT, "UI", "product_item.ui"),
    "cart": os.path.join(ROOT, "UI", "cart.ui"),
}

# Подключение к PostgreSQL
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", "5432")),
    "database": os.environ.get("DB_NAME", "demka"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", "1234"),
}

# Папка с ресурсами (иконки товаров по имени из Excel + заглушка)
RESOURCES_DIR = os.path.join(ROOT, "resources")
# Папка для загруженных фото товаров и заглушка
IMAGES_FOLDER = "product_images"
IMAGE_MAX_WIDTH = 300
IMAGE_MAX_HEIGHT = 200
PLACEHOLDER_IMAGE = "picture.png"

# Роли пользователей
ROLE_GUEST = "guest"
ROLE_CLIENT = "client"
ROLE_MANAGER = "manager"
ROLE_ADMINISTRATOR = "administrator"

# Статусы заказа для выпадающего списка (Модуль 4)
ORDER_STATUSES = ["новый", "в обработке", "доставляется", "выполнен", "отменён"]
