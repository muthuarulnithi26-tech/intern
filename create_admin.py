from controller.models import Admin, SessionLocal, create_tables
from werkzeug.security import generate_password_hash

create_tables()  # ensures tables exist

db = SessionLocal()

admin = db.query(Admin).filter_by(username="admin").first()
if not admin:
    admin = Admin(
        username="admin",
        password=generate_password_hash("admin123")
    )
    db.add(admin)
    db.commit()
    print("Admin created")
else:
    print("Admin already exists")

db.close()
