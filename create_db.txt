# Создание базы данных и таблиц. Запуск: python create_db.py (один раз в начале).
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import psycopg2
from App.config import DB_CONFIG

NAME = "demka"


def main():
    """Создаёт базу demka, если её нет, и выполняет скрипт DB.sql (создание таблиц)."""
    conn = psycopg2.connect(host=DB_CONFIG["host"], port=DB_CONFIG["port"], database="postgres",
                            user=DB_CONFIG["user"], password=DB_CONFIG["password"])
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (NAME,))
    if not cur.fetchone():
        cur.execute(f'CREATE DATABASE "{NAME}"')
        print("БД создана.")
    else:
        print("БД уже есть.")
    cur.close()
    conn.close()

    path = os.path.join(os.path.dirname(__file__), "DB.sql")
    with open(path, "r", encoding="utf-8") as f:
        sql = f.read()
    conn = psycopg2.connect(host=DB_CONFIG["host"], port=DB_CONFIG["port"], database=NAME,
                            user=DB_CONFIG["user"], password=DB_CONFIG["password"])
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()
    print("Таблицы созданы.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Ошибка:", e)
        sys.exit(1)
