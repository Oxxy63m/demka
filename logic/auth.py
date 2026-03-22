from App.db import auth_user


def login(login_text, password):
    return auth_user(login_text, password)


def get_guest_user():
    return {"full_name": "Гость", "role": "guest", "role_name": "guest", "role_id": 1}
