
from flask import Flask, render_template, request, redirect, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

from controller.models import (
    User, Song, Favorite, Playlist, PlaylistSong, RecentlyPlayed, Role
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
# CREATE DEFAULT ROLES
# -------------------------------------------------
def create_default_roles():
    db = SessionLocal()
    roles = ["admin", "creator", "listener"]
    for role_name in roles:
        existing = db.query(Role).filter_by(name=role_name).first()
        if not existing:
            db.add(Role(name=role_name))
    db.commit()
    db.close()

# Call it after creating tables
create_default_roles()


# -------------------------------------------------
# REGISTER
# -------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        db = SessionLocal()

        role_name = request.form["role"]  # creator / listener
        role = db.query(Role).filter_by(name=role_name).first()

        if not role:
            flash("Invalid role selected")
            db.close()
            return redirect("/register")

        user = User(
            username=request.form["username"],
            email_or_phone=request.form["email_or_phone"],
            password=generate_password_hash(request.form["password"]),
            role_id=role.id
        )

        db.add(user)
        db.commit()
        db.close()

        return redirect("/login")

    return render_template("register.html")

# -------------------------------------------------
# LOGIN
# -------------------------------------------------

# -------------------------------------------------
# LOGIN
# -------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        db = SessionLocal()

        # Fetch user by email or phone
        user = db.query(User).filter_by(
            email_or_phone=request.form["email_or_phone"]
        ).first()

        if user and check_password_hash(user.password, request.form["password"]):
            # Fetch role object to get role name
            role_obj = db.query(Role).filter_by(id=user.role_id).first()
            role_name = role_obj.name if role_obj else None

            if role_name:
                # Set session values
                session["user_id"] = user.id
                session["username"] = user.username
                session["role"] = role_name  # "admin", "creator", "listener"

                db.close()

                # Redirect based on role
                if role_name == "admin":
                    return redirect("/admin-dashboard")
                elif role_name == "creator":
                    return redirect("/creator-dashboard")
                elif role_name == "listener":
                    return redirect("/listener-dashboard")
                else:
                    # fallback
                    return redirect("/")

        flash("Invalid credentials")
        db.close()

    return render_template("login.html")
# -------------------------------------------------
# LOGOUT
# -------------------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# -------------------------------------------------
# CREATOR DASHBOARD
# -------------------------------------------------
@app.route("/creator-dashboard")
def creator_dashboard():
    if session.get("role") != "creator":
        return redirect("/login")

    db = SessionLocal()
    songs = db.query(Song).filter_by(uploader_id=session["user_id"]).all()
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
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

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
    db.refresh(song)  # get song.id

    # -----------------------------
    # Generate lyrics automatically
    # -----------------------------
    from generate_lyrics import update_song_lyrics
    update_song_lyrics(song.id, file_path)

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

@app.route("/delete-song/<int:song_id>", methods=["POST"])
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
    return redirect("/creator-dashboard")


# -------------------------------------------------
# LISTENER DASHBOARD
# -------------------------------------------------
@app.route("/listener-dashboard")
def listener_dashboard():
    if session.get("role") != "listener":
        return redirect("/login")

    db = SessionLocal()
    songs = db.query(Song).all()
    playlists = db.query(Playlist).filter_by(user_id=session["user_id"]).all()
    db.close()

    return render_template("listener_dashboard.html", songs=songs, playlists=playlists)
# -------------------------------------------------
# LOG RECENTLY PLAYED (AJAX)
# -------------------------------------------------
@app.route("/log-play/<int:song_id>", methods=["POST"])
def log_play(song_id):
    if session.get("role") != "listener":
        return jsonify({"error": "unauthorized"}), 403

    db = SessionLocal()
    old = db.query(RecentlyPlayed).filter_by(user_id=session["user_id"], song_id=song_id).first()

    if old:
        db.delete(old)

    db.add(RecentlyPlayed(user_id=session["user_id"], song_id=song_id))
    db.commit()
    db.close()

    return jsonify({"status": "ok"})

# -------------------------------------------------
# LIKE / FAVORITE SONG (AJAX)
# -------------------------------------------------
@app.route("/like-song/<int:song_id>", methods=["POST"])
def like_song(song_id):
    if session.get("role") != "listener":
        return jsonify({"error": "login required"}), 401

    db = SessionLocal()
    exists = db.query(Favorite).filter_by(user_id=session["user_id"], song_id=song_id).first()

    if not exists:
        db.add(Favorite(user_id=session["user_id"], song_id=song_id))
        db.commit()

    db.close()
    return jsonify({"status": "liked"})

@app.route("/unlike-song/<int:song_id>", methods=["POST"])
def unlike_song(song_id):
    if session.get("role") != "listener":
        return jsonify({"error": "login required"}), 401

    db = SessionLocal()
    fav = db.query(Favorite).filter_by(user_id=session["user_id"], song_id=song_id).first()
    if fav:
        db.delete(fav)
        db.commit()
    db.close()
    return jsonify({"status": "unliked"})

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

    if request.is_json:
        data = request.get_json()
        playlist = Playlist(name=data["playlist_name"], user_id=session["user_id"])
        db.add(playlist)
        db.commit()
        db.refresh(playlist)

        for sid in data["song_ids"]:
            db.add(PlaylistSong(playlist_id=playlist.id, song_id=int(sid)))

        db.commit()
        db.close()
        return jsonify({"message": "Playlist created successfully"})

    if request.method == "POST":
        playlist = Playlist(name=request.form["playlist_name"], user_id=session["user_id"])
        db.add(playlist)
        db.commit()
        db.refresh(playlist)

        for sid in request.form.getlist("song_ids"):
            db.add(PlaylistSong(playlist_id=playlist.id, song_id=int(sid)))

        db.commit()
        db.close()
        return redirect("/listener-dashboard")

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
    rows = db.query(Song).join(PlaylistSong, PlaylistSong.song_id == Song.id).filter(
        PlaylistSong.playlist_id == playlist_id
    ).all()

    songs = [{"id": s.id, "title": s.title, "file": "/static/" + s.file_path} for s in rows]
    db.close()
    return jsonify({"songs": songs})

# -------------------------------------------------
# VIEW PLAYLISTS
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
# ADMIN DASHBOARD
# -------------------------------------------------
from sqlalchemy.orm import joinedload
@app.route("/admin-dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect("/login")

    db = SessionLocal()

    # Eager-load role to avoid DetachedInstanceError
    users = db.query(User).options(joinedload(User.role)).all()
    songs = db.query(Song).all()
    total_users = len(users)
    total_songs = len(songs)
    total_playlists = db.query(Playlist).count()

    db.close()

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        total_songs=total_songs,
        total_playlists=total_playlists,
        users=users,
        songs=songs
    )

# -------------------------------------------------
# DELETE USER (ADMIN)
# -------------------------------------------------
@app.route("/admin/delete-user/<int:user_id>")
def admin_delete_user(user_id):
    if session.get("role") != "admin":
        return redirect("/login")

    db = SessionLocal()
    user = db.query(User).get(user_id)
    if user and user.role != "admin":
        db.delete(user)
        db.commit()
    db.close()
    return redirect("/admin-dashboard")

# -------------------------------------------------
# DELETE SONG (ADMIN)
# -------------------------------------------------
@app.route("/admin/delete-song/<int:song_id>")
def admin_delete_song(song_id):
    if session.get("role") != "admin":
        return redirect("/login")

    db = SessionLocal()
    song = db.query(Song).get(song_id)
    if song:
        try:
            os.remove(os.path.join("static", song.file_path))
        except:
            pass
        db.delete(song)
        db.commit()
    db.close()
    return redirect("/admin-dashboard")
# -------------------------------------------------
# RUN APP
# -------------------------------------------------
if __name__ == "__main__":   
    app.run(debug=True)
