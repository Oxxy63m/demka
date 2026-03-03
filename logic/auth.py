# Вход: проверка по БД и данные гостя
import os, sys
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)
from App.db import auth_user

def login(login_text, password):
    return auth_user(login_text, password)

def get_guest_user():
    return {"full_name": "Гость", "role": "guest"}
