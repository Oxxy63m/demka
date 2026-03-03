# =============================================================================
# СОЗДАНИЕ БАЗЫ ДАННЫХ (запускать первым, один раз)
# Запуск: python create_db.py
# Что делает: создаёт базу "demka" и все таблицы по скрипту DB.sql.
# Пароль и хост БД задаются в App/config.py (DB_CONFIG).
# =============================================================================
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import psycopg2
from App.config import DB_CONFIG

DB_NAME = "demka"


def main():
    connection_to_postgres = psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database="postgres",
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
    )
    connection_to_postgres.autocommit = True
    with connection_to_postgres.cursor() as cursor:
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
        if cursor.fetchone():
            print(f"БД '{DB_NAME}' уже существует.")
        else:
            cursor.execute(f'CREATE DATABASE "{DB_NAME}"')
            print(f"БД '{DB_NAME}' создана.")
    connection_to_postgres.close()

    schema_path = os.path.join(os.path.dirname(__file__), "DB.sql")
    with open(schema_path, "r", encoding="utf-8") as schema_file:
        schema_sql = schema_file.read()
    connection_to_demka = psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database=DB_NAME,
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
    )
    with connection_to_demka.cursor() as cursor:
        cursor.execute(schema_sql)
    connection_to_demka.commit()
    connection_to_demka.close()
    print("Таблицы созданы.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("Ошибка:", error)
        sys.exit(1)
