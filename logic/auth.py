# Логика входа: проверка логина/пароля в БД и возврат данных гостя.
import os
import sys

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)
from App.db import auth_user


def login(login_text, password):
    """Проверяет логин и пароль в БД. Возвращает словарь пользователя или None."""
    return auth_user(login_text, password)


def get_guest_user():
    """Возвращает словарь с данными пользователя «Гость» (full_name, role)."""
    return {"full_name": "Гость", "role": "guest"}
