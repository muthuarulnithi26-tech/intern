
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from controller.models import Base

DATABASE_URL = "sqlite:///app.db"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine)

def create_tables():
    Base.metadata.create_all(bind=engine)
