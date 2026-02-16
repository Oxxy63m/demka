import os

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", "5432")),
    "database": os.environ.get("DB_NAME", "demka"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", "1234"),
}

IMAGES_FOLDER = "product_images"
IMAGE_MAX_WIDTH = 300
IMAGE_MAX_HEIGHT = 200
PLACEHOLDER_IMAGE = "picture.png"

ROLE_GUEST = "guest"
ROLE_CLIENT = "client"
ROLE_MANAGER = "manager"
ROLE_ADMINISTRATOR = "administrator"
