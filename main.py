from flask import Flask, render_template, request, redirect, session, flash, url_for
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os

from controller.models import User, Admin, Song, SessionLocal, create_tables

# -------------------------------------------------
# APP SETUP
# -------------------------------------------------
app = Flask(__name__)
app.secret_key = "super-secret-key"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -------------------------------------------------
# DATABASE INIT
# -------------------------------------------------
create_tables()


@app.route("/")
def home():
    # If user logged in
    if "username" in session:
        if session.get("role") == "listener":
            return redirect(url_for("listener_dashboard"))
        elif session.get("role") == "creator":
            return redirect("/creator-dashboard")
        elif session.get("role") == "admin":
            return redirect("/admin-dashboard")
    # For new users
    return render_template("home.html")

# -------------------------------------------------
# REGISTER
# -------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    db = SessionLocal()
    if request.method == "POST":
        username = request.form.get("username")
        email_or_phone = request.form.get("email_or_phone")
        password = request.form.get("password")
        role = request.form.get("role")

        if not all([username, email_or_phone, password, role]):
            flash("All fields are required")
            return redirect("/register")

        if db.query(User).filter_by(email_or_phone=email_or_phone).first():
            flash("User already exists")
            return redirect("/register")

        user = User(
            username=username,
            email_or_phone=email_or_phone,
            password=generate_password_hash(password),
            role=role
        )
        db.add(user)
        db.commit()
        db.close()

        flash("Registration successful")
        return redirect("/login")

    db.close()
    return render_template("register.html")


# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    db = SessionLocal()
    if request.method == "POST":
        email_or_phone = request.form.get("email_or_phone")
        password = request.form.get("password")

        # Admin login
        admin = db.query(Admin).filter_by(username=email_or_phone).first()
        if admin and check_password_hash(admin.password, password):
            session.clear()
            session["username"] = admin.username
            session["role"] = "admin"
            db.close()
            return redirect("/admin-dashboard")

        # User login
        user = db.query(User).filter_by(email_or_phone=email_or_phone).first()
        if user and check_password_hash(user.password, password):
            session.clear()
            session["username"] = user.username
            session["role"] = user.role
            session["user_id"] = user.id
            db.close()

            if user.role == "creator":
                return redirect("/creator-dashboard")
            else:
                return redirect("/")   # ✅ LISTENER DASHBOARD

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
        return redirect("/")

    db = SessionLocal()
    search_query = request.args.get("search")
    user_id = session.get("user_id")

    if search_query:
        songs = db.query(Song).filter(
            Song.uploader_id == user_id,
            (Song.title.ilike(f"%{search_query}%")) |
            (Song.artist_name.ilike(f"%{search_query}%"))
        ).all()
    else:
        songs = db.query(Song).filter_by(uploader_id=user_id).all()

    db.close()
    return render_template(
        "creator_dashboard.html",
        songs=songs,
        username=session.get("username"),
        search_query=search_query
    )

# -------------------------------------------------
# UPLOAD SONG (PAGE)
# -------------------------------------------------
@app.route("/upload")
def upload_page():
    if session.get("role") != "creator":
        return redirect("/")
    return render_template("upload_song.html")

# -------------------------------------------------
# UPLOAD SONG (ACTION)
# -------------------------------------------------
@app.route("/upload-song", methods=["POST"])
def upload_song():
    if session.get("role") != "creator":
        return redirect("/")

    title = request.form.get("title")
    artist_name = request.form.get("artist_name")
    file = request.files.get("song_file")

    if not all([title, artist_name, file]):
        flash("All fields are required")
        return redirect("/upload")

    filename = secure_filename(file.filename)
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(save_path)

    db = SessionLocal()
    song = Song(
        title=title,
        artist_name=artist_name,
        file_path=f"uploads/{filename}",  # relative to static
        uploader_id=session.get("user_id")
    )
    db.add(song)
    db.commit()
    db.close()

    flash("Song uploaded successfully")
    return redirect("/creator-dashboard")

# -------------------------------------------------
# EDIT SONG
# -------------------------------------------------
@app.route("/edit-song/<int:song_id>")
def edit_song(song_id):
    if session.get("role") != "creator":
        return redirect("/")

    db = SessionLocal()
    song = db.query(Song).get(song_id)

    if not song or song.uploader_id != session.get("user_id"):
        db.close()
        flash("Unauthorized access")
        return redirect("/creator-dashboard")

    db.close()
    return render_template("edit_song.html", song=song)

@app.route("/update-song/<int:song_id>", methods=["POST"])
def update_song(song_id):
    if session.get("role") != "creator":
        return redirect("/")

    db = SessionLocal()
    song = db.query(Song).get(song_id)

    if not song or song.uploader_id != session.get("user_id"):
        db.close()
        flash("Unauthorized update")
        return redirect("/creator-dashboard")

    song.title = request.form.get("title")
    song.artist_name = request.form.get("artist_name")
    db.commit()
    db.close()

    flash("Song updated")
    return redirect("/creator-dashboard")

# -------------------------------------------------
# DELETE SONG
# -------------------------------------------------
@app.route("/delete-song/<int:song_id>", methods=["POST"])
def delete_song(song_id):
    if session.get("role") != "creator":
        return redirect("/")

    db = SessionLocal()
    song = db.query(Song).filter_by(
        id=song_id,
        uploader_id=session.get("user_id")
    ).first()

    if not song:
        db.close()
        flash("Unauthorized action")
        return redirect("/creator-dashboard")

    file_full_path = os.path.join("static", song.file_path)
    if os.path.exists(file_full_path):
        os.remove(file_full_path)

    db.delete(song)
    db.commit()
    db.close()

    flash("Song deleted")
    return redirect("/creator-dashboard")

# -------------------------------------------------
# PROFILE
# -------------------------------------------------
@app.route("/profile")
def profile():
    if "username" not in session:
        return redirect("/login")

    db = SessionLocal()
    total_songs = db.query(Song).count()
    db.close()

    return render_template(
        "profile.html",
        username=session["username"],
        role=session["role"],
        total_songs=total_songs,
        total_playlists=0
    )

# -------------------------------------------------
# PLAYLIST (BASIC)
# -------------------------------------------------
@app.route("/playlists")
def playlists():
    if "username" not in session:
        return redirect("/login")

    return render_template("playlist.html", playlists=[])
# -------------------------------------------------
# LISTENER DASHBOARD
# -------------------------------------------------
@app.route("/listener-dashboard")
def listener_dashboard():
    if session.get("role") != "listener":
        return redirect("/login")

    db = SessionLocal()
    search_query = request.args.get("search")
    songs = []

    if search_query:
        songs = db.query(Song).filter(
            (Song.title.ilike(f"%{search_query}%")) |
            (Song.artist_name.ilike(f"%{search_query}%"))
        ).all()

    db.close()
    return render_template(
        "listener_dashboard.html",
        username=session.get("username"),
        search_query=search_query,
        songs=songs
    )

# -------------------------------------------------
# ADMIN DASHBOARD
# -------------------------------------------------
@app.route("/admin-dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect("/login")

    db = SessionLocal()
    users = db.query(User).all()
    songs = db.query(Song).all()
    db.close()

    return render_template("admin_dashboard.html", users=users, songs=songs)

# -------------------------------------------------
# ADMIN DELETE SONG
# -------------------------------------------------
@app.route("/admin/delete-song/<int:song_id>", methods=["POST"])
def admin_delete_song(song_id):
    if session.get("role") != "admin":
        return redirect("/login")

    db = SessionLocal()
    song = db.query(Song).get(song_id)

    if song:
        file_full_path = os.path.join("static", song.file_path)
        if os.path.exists(file_full_path):
            os.remove(file_full_path)
        db.delete(song)
        db.commit()

    db.close()
    return redirect("/admin-dashboard")

# -------------------------------------------------
# ADMIN DELETE USER
# -------------------------------------------------
@app.route("/admin/delete-user/<int:user_id>", methods=["POST"])
def admin_delete_user(user_id):
    if session.get("role") != "admin":
        return redirect("/login")

    db = SessionLocal()
    user = db.query(User).get(user_id)

    if user:
        db.delete(user)
        db.commit()

    db.close()
    return redirect("/admin-dashboard")

# -------------------------------------------------
# RUN
# -------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
