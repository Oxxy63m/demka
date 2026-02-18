# Создание БД demka и таблиц. Запуск: python create_db.py
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import psycopg2
from App.config import DB_CONFIG

DB_NAME = "demka"


def main():
    conn = psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database="postgres",
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
    )
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
        if cur.fetchone():
            print(f"БД '{DB_NAME}' уже существует.")
        else:
            cur.execute(f'CREATE DATABASE "{DB_NAME}"')
            print(f"БД '{DB_NAME}' создана.")
    conn.close()

    schema_path = os.path.join(os.path.dirname(__file__), "DB.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    conn = psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database=DB_NAME,
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
    )
    with conn.cursor() as cur:
        cur.execute(schema_sql)
    conn.commit()
    conn.close()
    print("Таблицы созданы.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Ошибка:", e)
        sys.exit(1)
