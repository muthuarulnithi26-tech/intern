
from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

from controller.models import (
    User, Song, Favorite, Playlist, PlaylistSong, RecentlyPlayed
)
from controller.database import SessionLocal, create_tables

app = Flask(__name__)
app.secret_key = "super-secret-key"

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

create_tables()

# -------------------------------------------------
# HOME
# -------------------------------------------------
@app.route("/")
def home():
    if "role" in session:
        if session["role"] == "creator":
            return redirect("/creator-dashboard")
        if session["role"] == "listener":
            return redirect("/listener-dashboard")
        if session["role"] == "admin":
            return redirect("/admin-dashboard")
    return render_template("home.html")

# -------------------------------------------------
# AUTH
# -------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    db = SessionLocal()
    if request.method == "POST":
        user = User(
            username=request.form["username"],
            email_or_phone=request.form["email_or_phone"],
            password=generate_password_hash(request.form["password"]),
            role=request.form["role"]
        )
        db.add(user)
        db.commit()
        db.close()
        return redirect("/login")
    db.close()
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    db = SessionLocal()
    if request.method == "POST":
        user = db.query(User).filter_by(
            email_or_phone=request.form["email_or_phone"]
        ).first()

        if user and check_password_hash(user.password, request.form["password"]):
            session["user_id"] = user.id
            session["username"] = user.username
            session["role"] = user.role
            db.close()
            return redirect("/")
    db.close()
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# -------------------------------------------------
# CREATOR
# -------------------------------------------------
@app.route("/creator-dashboard")
def creator_dashboard():
    if session.get("role") != "creator":
        return redirect("/login")

    db = SessionLocal()
    songs = db.query(Song).filter(
        Song.uploader_id == session["user_id"]
    ).all()
    db.close()

    return render_template("creator_dashboard.html", songs=songs)


@app.route("/upload")
def upload_page():
    if session.get("role") != "creator":
        return redirect("/login")
    return render_template("upload_song.html")


@app.route("/upload-song", methods=["POST"])
def upload_song():
    if session.get("role") != "creator":
        return redirect("/login")

    file = request.files.get("song_file")
    if not file or file.filename == "":
        flash("Please select a song file")
        return redirect("/upload")

    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    db = SessionLocal()
    song = Song(
        title=request.form["title"],
        artist_name=request.form["artist_name"],
        genre=request.form["genre"],
        file_path=f"uploads/{filename}",
        uploader_id=session["user_id"]
    )

    db.add(song)
    db.commit()
    db.close()

    return redirect("/creator-dashboard")
@app.route("/edit-song/<int:song_id>")
def edit_song_page(song_id):
    if session.get("role") != "creator":
        return redirect("/login")

    db = SessionLocal()
    song = db.query(Song).filter(
        Song.id == song_id,
        Song.uploader_id == session["user_id"]
    ).first()
    db.close()

    if not song:
        return redirect("/creator-dashboard")

    return render_template("edit_song.html", song=song)
@app.route("/update-song/<int:song_id>", methods=["POST"])
def update_song(song_id):
    if session.get("role") != "creator":
        return redirect("/login")

    db = SessionLocal()
    song = db.query(Song).filter(
        Song.id == song_id,
        Song.uploader_id == session["user_id"]
    ).first()

    if song:
        song.title = request.form["title"]
        song.artist_name = request.form["artist_name"]
        song.genre = request.form["genre"]

        db.commit()

    db.close()
    return redirect("/creator-dashboard")


@app.route("/delete-song/<int:song_id>")
def delete_song(song_id):
    if session.get("role") != "creator":
        return redirect("/login")

    db = SessionLocal()
    song = db.query(Song).get(song_id)

    if song and song.uploader_id == session["user_id"]:
        try:
            os.remove(os.path.join("static", song.file_path))
        except:
            pass
        db.delete(song)
        db.commit()

    db.close()
    return redirect("/creator-dashboard")

# -------------------------------------------------
# LISTENER
# -------------------------------------------------
@app.route("/listener-dashboard")
def listener_dashboard():
    if session.get("role") != "listener":
        return redirect("/login")

    db = SessionLocal()
    songs = db.query(Song).all()

    recently_played = (
        db.query(RecentlyPlayed)
        .filter_by(user_id=session["user_id"])
        .order_by(RecentlyPlayed.played_at.desc())
        .limit(5)
        .all()
    )

    playlists = db.query(Playlist).filter_by(
        user_id=session["user_id"]
    ).all()

    db.close()

    return render_template(
        "listener_dashboard.html",
        songs=songs,
        recently_played=recently_played,
        playlists=playlists
    )


@app.route("/play/<int:song_id>")
def play_song(song_id):
    if session.get("role") != "listener":
        return redirect("/login")

    db = SessionLocal()

    old = db.query(RecentlyPlayed).filter_by(
        user_id=session["user_id"],
        song_id=song_id
    ).first()

    if old:
        db.delete(old)

    db.add(RecentlyPlayed(
        user_id=session["user_id"],
        song_id=song_id
    ))

    db.commit()
    db.close()

    return redirect("/listener-dashboard")


@app.route("/favorite/<int:song_id>")
def toggle_favorite(song_id):
    if session.get("role") != "listener":
        return redirect("/login")

    db = SessionLocal()

    fav = db.query(Favorite).filter_by(
        user_id=session["user_id"],
        song_id=song_id
    ).first()

    if fav:
        db.delete(fav)
    else:
        db.add(Favorite(
            user_id=session["user_id"],
            song_id=song_id
        ))

    db.commit()
    db.close()

    return redirect("/listener-dashboard")

# -------------------------------------------------
# PLAYLIST
# -------------------------------------------------
@app.route("/create-playlist", methods=["POST"])
def create_playlist():
    if session.get("role") != "listener":
        return redirect("/login")

    db = SessionLocal()
    playlist = Playlist(
        name=request.form["name"],
        user_id=session["user_id"]
    )
    db.add(playlist)
    db.commit()
    db.close()

    return redirect("/listener-dashboard")


@app.route("/playlist/<int:playlist_id>")
def view_playlist(playlist_id):
    if session.get("role") != "listener":
        return redirect("/login")

    db = SessionLocal()
    playlist = db.query(Playlist).filter_by(
        id=playlist_id,
        user_id=session["user_id"]
    ).first()
    db.close()

    if not playlist:
        return redirect("/listener-dashboard")

    return render_template("playlist.html", playlist=playlist)

# -------------------------------------------------
# ADMIN
# -------------------------------------------------
@app.route("/admin-dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect("/login")
    return "Admin Dashboard"


if __name__ == "__main__":
    app.run(debug=True)
