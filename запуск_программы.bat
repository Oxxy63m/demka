@echo off
chcp 65001 >nul
echo Запуск программы...
python main.py
if errorlevel 1 (
    echo.
    echo Ошибка. Проверьте: 1) Установлен ли Python  2) Выполнен ли pip install -r requirements.txt  3) Создана ли БД: python create_db.py
    pause
)
