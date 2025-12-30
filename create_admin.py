
from werkzeug.security import generate_password_hash
from controller.database import SessionLocal, engine
from controller.models import Base, User, Role

# Ensure tables exist
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# -------------------------
# Ensure ADMIN role exists
# -------------------------
admin_role = db.query(Role).filter_by(name="admin").first()
if not admin_role:
    admin_role = Role(name="admin")
    db.add(admin_role)
    db.commit()
    db.refresh(admin_role)

# -------------------------
# Create admin user
# -------------------------
existing_admin = db.query(User).filter_by(username="admin").first()

if not existing_admin:
    admin = User(
        username="admin",
        email_or_phone="admin@gmail.com",  
        password=generate_password_hash("admin123"),
        role_id=admin_role.id
    )
    db.add(admin)
    db.commit()
    print("✅ Admin created successfully")
else:
    print("ℹ️ Admin already exists")

db.close()
