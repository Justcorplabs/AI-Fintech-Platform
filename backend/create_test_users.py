from sqlalchemy import select

from app.db.database import SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash


USERS = [
    {
        "email": "admin@test.com",
        "name": "System Admin",
        "role": UserRole.admin,
    },
    {
        "email": "analyst@test.com",
        "name": "Fraud Analyst",
        "role": UserRole.analyst,
    },
    {
        "email": "recruiter@test.com",
        "name": "HR Recruiter",
        "role": UserRole.recruiter,
    },
]

PASSWORD = "SecurePass123"


db = SessionLocal()

try:
    for u in USERS:
        existing = db.scalar(
            select(User).where(User.email == u["email"])
        )

        if existing:
            existing.role = u["role"]
            existing.full_name = u["name"]
            existing.hashed_password = get_password_hash(PASSWORD)
            existing.is_active = True
            print(f"Updated {u['email']} ({u['role'].value})")
        else:
            db.add(
                User(
                    email=u["email"],
                    full_name=u["name"],
                    hashed_password=get_password_hash(PASSWORD),
                    role=u["role"],
                    is_active=True,
                )
            )
            print(f"Created {u['email']} ({u['role'].value})")

    db.commit()

finally:
    db.close()

print("\nDone.")