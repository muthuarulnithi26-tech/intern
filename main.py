from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os

from controller.database import SessionLocal
from controller.models import create_tables, User, BroadcasterProfile, Artist, Song

app = Flask(__name__)
app.secret_key = "secret-key"

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Ensure database tables exist
create_tables()

def get_db():
    return SessionLocal()

# ---------------- HOME ----------------
@app.route("/")
def home():
    db = get_db()
    songs = db.query(Song).all()
    return render_template("home.html", songs=songs)

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    db = get_db()  # Create session here
    if request.method == "POST":
        username = request.form.get("username")
        email_or_phone = request.form.get("email_or_phone")  # matches your HTML
        password = request.form.get("password")

        if not username or not email_or_phone or not password:
            flash("All fields are required")
            return redirect("/register")

        existing_user = db.query(User).filter_by(email_or_phone=email_or_phone).first()
        if existing_user:
            flash("User already exists")
            return redirect("/register")

        user = User(
            username=username,
            email_or_phone=email_or_phone,
            password=generate_password_hash(password),
            role="listener"
        )
        db.add(user)
        db.commit()

        flash("Registration successful. Please login.")
        return redirect("/login")

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    db = get_db()  # Create session here
    if request.method == "POST":
        email_or_phone = request.form.get("email_or_phone")
        password = request.form.get("password")

        user = db.query(User).filter_by(email_or_phone=email_or_phone).first()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["role"] = user.role
            return redirect("/")
        flash("Invalid credentials")
    return render_template("login.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- PROFILE ----------------
@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("profile.html")

# ---------------- BECOME BROADCASTER ----------------
@app.route("/become-broadcaster", methods=["GET", "POST"])
def become_broadcaster():
    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") == "broadcaster":
        flash("You are already a broadcaster")
        return redirect("/profile")

    db = get_db()
    if request.method == "POST":
        profile = BroadcasterProfile(
            user_id=session["user_id"],
            channel_name=request.form.get("channel"),
            description=request.form.get("description")
        )
        db.add(profile)

        user = db.query(User).get(session["user_id"])
        user.role = "broadcaster"

        db.commit()
        session["role"] = "broadcaster"
        return redirect("/upload-song")

    return render_template("become_broadcaster.html")

# ---------------- UPLOAD SONG ----------------
@app.route("/upload-song", methods=["GET", "POST"])
def upload_song():
    if "user_id" not in session or session.get("role") != "broadcaster":
        return redirect("/")

    db = get_db()
    if request.method == "POST":
        artist_name = request.form.get("artist")
        artist = db.query(Artist).filter_by(name=artist_name).first()

        if not artist:
            artist = Artist(name=artist_name)
            db.add(artist)
            db.commit()

        file = request.files.get("song")
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)

            song = Song(
                title=request.form.get("title"),
                file_path=file_path,
                artist_id=artist.id,
                broadcaster_id=session["user_id"]
            )
            db.add(song)
            db.commit()
            flash("Song uploaded successfully")

        return redirect("/upload-song")

    return render_template("upload_song.html")

if __name__ == "__main__":
    app.run(debug=True)
