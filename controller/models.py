
from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Text
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

# ------------------------------
# ROLE
# ------------------------------
class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)

    users = relationship("User", back_populates="role")


# ------------------------------
# USER
# ------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    email_or_phone = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    role = relationship("Role", back_populates="users")

    songs = relationship("Song", back_populates="uploader", cascade="all, delete")
    playlists = relationship("Playlist", back_populates="user", cascade="all, delete")


# ------------------------------
# SONG
# ------------------------------
class Song(Base):
    __tablename__ = "songs"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    artist_name = Column(String, nullable=False)
    genre = Column(String)
    language = Column(String)
    file_path = Column(String, nullable=False)

    # ✅ Lyrics added (this fixes your Jinja error)
    lyrics = Column(Text, nullable=True)

    uploader_id = Column(Integer, ForeignKey("users.id"))
    uploader = relationship("User", back_populates="songs")


# ------------------------------
# FAVORITES
# ------------------------------
class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    song_id = Column(Integer, ForeignKey("songs.id"))

    song = relationship("Song")


# ------------------------------
# PLAYLIST
# ------------------------------
class Playlist(Base):
    __tablename__ = "playlists"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="playlists")
    songs = relationship("PlaylistSong", back_populates="playlist", cascade="all, delete")


# ------------------------------
# PLAYLIST SONGS
# ------------------------------
class PlaylistSong(Base):
    __tablename__ = "playlist_songs"

    id = Column(Integer, primary_key=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id"))
    song_id = Column(Integer, ForeignKey("songs.id"))

    playlist = relationship("Playlist", back_populates="songs")
    song = relationship("Song")


# ------------------------------
# RECENTLY PLAYED
# ------------------------------
class RecentlyPlayed(Base):
    __tablename__ = "recently_played"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    song_id = Column(Integer, ForeignKey("songs.id"))
    played_at = Column(DateTime, default=datetime.utcnow)

    song = relationship("Song")
