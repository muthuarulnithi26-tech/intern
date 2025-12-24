
from sqlalchemy import Column, Integer, String, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from werkzeug.security import generate_password_hash

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    email_or_phone = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False)  # 'listener' or 'creator'
    songs = relationship("Song", backref="uploader")

class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)

class Song(Base):
    __tablename__ = "songs"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    artist_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)  # store only filename
    uploader_id = Column(Integer, ForeignKey("users.id"))

# DB setup
engine = create_engine("sqlite:///app.db", echo=False)
SessionLocal = sessionmaker(bind=engine)

def create_tables():
    Base.metadata.create_all(engine)

def create_admin():
    db = SessionLocal()
    if not db.query(Admin).filter_by(username="admin").first():
        admin = Admin(
            username="admin",
            password=generate_password_hash("admin123")
        )
        db.add(admin)
        db.commit()
    db.close()
