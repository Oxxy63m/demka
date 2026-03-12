# Вход: проверка логина/пароля в БД, данные гостя.
from App.db import auth_user


def login(login_text, password):
    """Проверяет логин и пароль в БД. Возвращает словарь пользователя или None."""
    return auth_user(login_text, password)


def get_guest_user():
    """Возвращает словарь с данными пользователя «Гость». role_id = 1."""
    return {"full_name": "Гость", "role": "guest", "role_name": "guest", "role_id": 1}
