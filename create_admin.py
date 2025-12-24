from werkzeug.security import generate_password_hash
from controller.models import Admin, SessionLocal

db = SessionLocal()

admin = db.query(Admin).filter_by(username="admin").first()

if not admin:
    admin = Admin(
        username="admin",
        password=generate_password_hash("admin123")
    )
    db.add(admin)
    db.commit()
    print("✅ Admin created successfully")
else:
    print("⚠️ Admin already exists")

db.close()
