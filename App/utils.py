# App/utils.py — общие утилиты: путь к корню проекта (ROOT) для ресурсов и картинок
import os

# Корень проекта (папка, в которой лежат App, UI, import)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
