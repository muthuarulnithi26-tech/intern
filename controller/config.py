
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "..", "instance")

DATABASE_URL = f"sqlite:///{os.path.join(INSTANCE_DIR, 'music.db')}"
