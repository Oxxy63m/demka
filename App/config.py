# =============================================================================
# НАСТРОЙКИ ПРОГРАММЫ (единственное место, где менять пути и пароль БД)
# Что менять: DATA_DIR — папка с Excel и картинками; DB_CONFIG — пароль и
# хост PostgreSQL. Остальное обычно не трогать.
# =============================================================================
import os

# Корень проекта (для путей к UI)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Папка с Excel и фото (импорт и отображение картинок). Путь нормализован.
DATA_DIR = os.path.normpath(os.path.abspath(os.environ.get("DATA_DIR", r"C:\Users\user\Documents\fuckdemoexam\Модуль 1\import")))
PHOTOS_DIR = DATA_DIR  # те же файлы — фото ищем здесь же
# Иконка приложения (в заголовке окна)
APP_ICON = os.path.join(DATA_DIR, "icon.ico")
# Логотип на странице входа
LOGIN_LOGO = os.path.join(DATA_DIR, "icon.png")
# Пути к .ui файлам (папка ui в корне проекта)
UI = {
    "login": os.path.join(ROOT, "ui", "login.ui"),
    "main": os.path.join(ROOT, "ui", "main.ui"),
    "orders": os.path.join(ROOT, "ui", "orders_list.ui"),
    "order": os.path.join(ROOT, "ui", "order_form.ui"),
    "prod": os.path.join(ROOT, "ui", "product_form.ui"),
    "card": os.path.join(ROOT, "ui", "product_item.ui"),
    "cart": os.path.join(ROOT, "ui", "cart.ui"),
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
# Плейсхолдер, если в Excel не указано имя фото (и для отображения при отсутствии файла)
PLACEHOLDER_IMAGE = "picture.png"

# Роли пользователей
ROLE_GUEST = "guest"
ROLE_CLIENT = "client"
ROLE_MANAGER = "manager"
ROLE_ADMINISTRATOR = "administrator"

# Статусы заказа для выпадающего списка (Модуль 4)
ORDER_STATUSES = ["новый", "в обработке", "доставляется", "выполнен", "отменён"]
# Пункты выдачи для оформления заказа (клиент)
PICKUP_POINTS = ["Пункт выдачи 1", "Пункт выдачи 2", "Пункт выдачи 3"]
