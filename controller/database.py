
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from controller.models import Base

# Project root (one level above controller/)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Instance folder at project root
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)

DATABASE_URL = f"sqlite:///{os.path.join(INSTANCE_DIR, 'music.db')}"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine)

def create_tables():
    Base.metadata.create_all(bind=engine)
