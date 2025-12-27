
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    email_or_phone = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False)

class Song(Base):
    __tablename__ = "songs"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    artist_name = Column(String, nullable=False)
    genre = Column(String)
    language = Column(String)
    file_path = Column(String, nullable=False)
    uploader_id = Column(Integer, ForeignKey("users.id"))

class Favorite(Base):
    __tablename__ = "favorites"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    song_id = Column(Integer, ForeignKey("songs.id"))

class Playlist(Base):
    __tablename__ = "playlists"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))

class PlaylistSong(Base):
    __tablename__ = "playlist_songs"
    id = Column(Integer, primary_key=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id"))
    song_id = Column(Integer, ForeignKey("songs.id"))

    
from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

class RecentlyPlayed(Base):
    __tablename__ = "recently_played"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    song_id = Column(Integer, ForeignKey("songs.id"))
    played_at = Column(DateTime, default=datetime.utcnow)

    song = relationship("Song")
