from sqlalchemy import Column, Integer, String, ForeignKey
from controller.database import Base, engine

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    email_or_phone = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="listener")  # listener | broadcaster


class BroadcasterProfile(Base):
    __tablename__ = "broadcaster_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

    channel_name = Column(String, nullable=False)
    description = Column(String)


class Artist(Base):
    __tablename__ = "artists"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)


class Song(Base):
    __tablename__ = "songs"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    file_path = Column(String, nullable=False)

    artist_id = Column(Integer, ForeignKey("artists.id"))
    broadcaster_id = Column(Integer, ForeignKey("users.id"))


def create_tables():
    Base.metadata.create_all(bind=engine)
