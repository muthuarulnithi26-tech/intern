from flask import Flask, render_template, request, redirect, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

from controller.models import (
    User, Song, Favorite, Playlist, PlaylistSong, RecentlyPlayed
)
from controller.database import SessionLocal, create_tables

# -------------------------------------------------
# APP SETUP
# -------------------------------------------------
app = Flask(__name__)
app.secret_key = "super-secret-key"

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
    return render_template("home.html")

# -------------------------------------------------
# AUTH
# -------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        db = SessionLocal()
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
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        db = SessionLocal()
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
    songs = db.query(Song).filter_by(
        uploader_id=session["user_id"]
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
    song = db.query(Song).filter_by(
        id=song_id,
        uploader_id=session["user_id"]
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
    song = db.query(Song).filter_by(
        id=song_id,
        uploader_id=session["user_id"]
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
        except FileNotFoundError:
            pass
        db.delete(song)
        db.commit()

    db.close()
    return redirect("/creator_dashboard")
# -------------------------------------------------
# LISTENER DASHBOARD
# -------------------------------------------------
@app.route("/listener-dashboard")
def listener_dashboard():
    if session.get("role") != "listener":
        return redirect("/login")

    db = SessionLocal()

    songs = db.query(Song).all()
    playlists = db.query(Playlist).filter_by(
        user_id=session["user_id"]
    ).all()

    db.close()

    return render_template(
        "listener_dashboard.html",
        songs=songs,
        playlists=playlists
    )

# -------------------------------------------------
# LOG RECENTLY PLAYED (AJAX)
# -------------------------------------------------
@app.route("/log-play/<int:song_id>", methods=["POST"])
def log_play(song_id):
    if session.get("role") != "listener":
        return jsonify({"error": "unauthorized"}), 403

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

    return jsonify({"status": "ok"})

# -------------------------------------------------
# LIKE / FAVOURITE SONG (AJAX)
# -------------------------------------------------
@app.route("/like-song/<int:song_id>", methods=["POST"])
def like_song(song_id):
    if session.get("role") != "listener":
        return jsonify({"error": "login required"}), 401

    db = SessionLocal()

    exists = db.query(Favorite).filter_by(
        user_id=session["user_id"],
        song_id=song_id
    ).first()

    if not exists:
        db.add(Favorite(
            user_id=session["user_id"],
            song_id=song_id
        ))
        db.commit()

    db.close()
    return jsonify({"status": "liked"})

# -------------------------------------------------
# FAVOURITE PAGE
# -------------------------------------------------
@app.route("/favourite")
def favourite():
    if session.get("role") != "listener":
        return redirect("/login")

    db = SessionLocal()

    songs = (
        db.query(Song)
        .join(Favorite, Favorite.song_id == Song.id)
        .filter(Favorite.user_id == session["user_id"])
        .all()
    )

    db.close()
    return render_template("favourite.html", songs=songs)

# -------------------------------------------------
# CREATE PLAYLIST (FORM + AJAX)
# -------------------------------------------------
@app.route("/create-playlist", methods=["GET", "POST"])
def create_playlist():
    if session.get("role") != "listener":
        return redirect("/login")

    db = SessionLocal()

    # -------- AJAX REQUEST --------
    if request.is_json:
        data = request.get_json()

        playlist = Playlist(
            name=data["playlist_name"],
            user_id=session["user_id"]
        )
        db.add(playlist)
        db.commit()
        db.refresh(playlist)

        for sid in data["song_ids"]:
            db.add(PlaylistSong(
                playlist_id=playlist.id,
                song_id=int(sid)
            ))

        db.commit()
        db.close()
        return jsonify({"message": "Playlist created successfully"})

    # -------- NORMAL FORM POST --------
    if request.method == "POST":
        playlist = Playlist(
            name=request.form["playlist_name"],
            user_id=session["user_id"]
        )
        db.add(playlist)
        db.commit()
        db.refresh(playlist)

        for sid in request.form.getlist("song_ids"):
            db.add(PlaylistSong(
                playlist_id=playlist.id,
                song_id=int(sid)
            ))

        db.commit()
        db.close()
        return redirect("/listener-dashboard")

    # -------- GET PAGE --------
    songs = db.query(Song).all()
    db.close()
    return render_template("create_playlist.html", songs=songs)

# -------------------------------------------------
# PLAYLIST SONGS (AJAX)
# -------------------------------------------------
@app.route("/playlist-songs/<int:playlist_id>")
def playlist_songs(playlist_id):
    if session.get("role") != "listener":
        return jsonify({"songs": []})

    db = SessionLocal()

    rows = (
        db.query(Song)
        .join(PlaylistSong, PlaylistSong.song_id == Song.id)
        .filter(PlaylistSong.playlist_id == playlist_id)
        .all()
    )

    songs = []
    for song in rows:
        songs.append({
            "id": song.id,
            "title": song.title,
            "file": "/static/" + song.file_path
        })

    db.close()
    return jsonify({"songs": songs})
# -------------------------------------------------
# VIEW ALL PLAYLISTS
# -------------------------------------------------
@app.route("/playlist")
def view_playlists():
    if session.get("role") != "listener":
        return redirect("/login")

    db = SessionLocal()
    playlists = db.query(Playlist).filter_by(user_id=session["user_id"]).all()
    db.close()
    return render_template("playlist.html", playlists=playlists)

# -------------------------------------------------
# DELETE PLAYLIST
# -------------------------------------------------
@app.route("/delete-playlist/<int:playlist_id>", methods=["POST"])
def delete_playlist(playlist_id):
    if session.get("role") != "listener":
        return jsonify({"error":"unauthorized"}), 403

    db = SessionLocal()
    playlist = db.query(Playlist).filter_by(id=playlist_id, user_id=session["user_id"]).first()
    if playlist:
        # Delete all playlist songs first
        db.query(PlaylistSong).filter_by(playlist_id=playlist.id).delete()
        db.delete(playlist)
        db.commit()
    db.close()
    return redirect("/playlist")

# -------------------------------------------------
# EDIT PLAYLIST
# -------------------------------------------------
@app.route("/edit-playlist/<int:playlist_id>", methods=["GET","POST"])
def edit_playlist(playlist_id):
    if session.get("role") != "listener":
        return redirect("/login")

    db = SessionLocal()
    playlist = db.query(Playlist).filter_by(id=playlist_id, user_id=session["user_id"]).first()
    if not playlist:
        db.close()
        return redirect("/playlist")

    songs = db.query(Song).all()

    if request.method == "POST":
        playlist.name = request.form["playlist_name"]
        db.query(PlaylistSong).filter_by(playlist_id=playlist.id).delete()
        for sid in request.form.getlist("song_ids"):
            db.add(PlaylistSong(playlist_id=playlist.id, song_id=int(sid)))
        db.commit()
        db.close()
        return redirect("/playlist")

    # Get existing song IDs
    existing_song_ids = [ps.song_id for ps in db.query(PlaylistSong).filter_by(playlist_id=playlist.id).all()]
    db.close()
    return render_template("edit_playlist.html", playlist=playlist, songs=songs, existing_song_ids=existing_song_ids)
# -------------------------------------------------
# SEARCH SONGS (AJAX)
# -------------------------------------------------
@app.route("/search-songs")
def search_songs():
    if session.get("role") != "listener":
        return jsonify({"songs": []})

    query = request.args.get("q", "").strip()
    db = SessionLocal()

    if query:
        results = db.query(Song).filter(
            (Song.title.ilike(f"%{query}%")) | (Song.artist_name.ilike(f"%{query}%"))
        ).all()
    else:
        results = []

    songs = [{"id": s.id, "title": s.title, "file": "/static/" + s.file_path} for s in results]
    db.close()
    return jsonify({"songs": songs})

# -------------------------------------------------
# RUN APP
# -------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
