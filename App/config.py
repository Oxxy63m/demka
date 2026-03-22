# config.py
import os

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

DATA_DIR = "resources"
APP_ICON = "resources/icon.ico"
RESOURCES_DIR = os.path.join(_ROOT, "resources")
PLACEHOLDER_PHOTO = os.path.join(RESOURCES_DIR, "picture.png")

UI = {
    "login": "ui/login.ui",
    "main": "ui/main.ui",
    "orders": "ui/orders_list.ui",
    "order": "ui/order_form.ui",
    "order_card": "ui/order_item.ui",
    "prod": "ui/product_form.ui",
    "card": "ui/product_item.ui",
}


def ui_path(key: str) -> str:
    """Абсолютный путь к .ui (loadUiType иначе может вернуть None, если cwd не корень проекта)."""
    return os.path.normpath(os.path.join(_ROOT, UI[key].replace("/", os.sep)))

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "demka",
    "user": "postgres",
    "password": "1234",
}

ROLE_GUEST = "guest"
ROLE_CLIENT = "client"
ROLE_MANAGER = "manager"
# Как в типичной БД (roles.role_name); короткий "admin" тоже поддерживаем в проверках.
ROLE_ADMINISTRATOR = "administrator"

ROLE_TITLE_RU = {
    "admin": "Администратор",
    "administrator": "Администратор",
    "manager": "Менеджер",
    "client": "Клиент",
    "guest": "Гость",
}


def is_admin_role(role_name) -> bool:
    r = str(role_name or "").strip().lower()
    return r == ROLE_ADMINISTRATOR or r == "admin"


def is_manager_or_admin(role_name) -> bool:
    r = str(role_name or "").strip().lower()
    return r == ROLE_MANAGER or is_admin_role(r)


def role_title_ru(role_name):
    if not role_name:
        return ROLE_TITLE_RU["guest"]
    return ROLE_TITLE_RU.get(str(role_name).strip().lower(), str(role_name))
