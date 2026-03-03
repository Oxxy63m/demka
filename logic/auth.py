# Вход в систему: проверка логина/пароля по БД, данные гостя (без входа).
import os
import sys

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from App.db import auth_user as _db_auth_user


def login(login_text, password):
    """Проверка логина и пароля. Возвращает словарь user или None."""
    return _db_auth_user(login_text, password)


def get_guest_user():
    """Данные пользователя «Гость»."""
    return {"full_name": "Гость", "role": "guest"}
