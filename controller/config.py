import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")

os.makedirs(INSTANCE_DIR, exist_ok=True)

DATABASE_URL = f"sqlite:///{os.path.join(INSTANCE_DIR, 'music.db')}"

# ADMIN CREDENTIALS (hardcoded)
ADMIN_EMAIL = "admin@isai.com"
ADMIN_PASSWORD = "admin123"
