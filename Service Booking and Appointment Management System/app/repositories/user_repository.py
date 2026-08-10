from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import get_password_hash


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, email: str, full_name: str, password: str, role: str, phone: str, address: str) -> User:
        user = User(
            email=email,
            full_name=full_name,
            hashed_password=get_password_hash(password),
            role=role,
            phone=phone,
            address=address,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email, User.is_deleted.is_(False)).first()

    def get_by_phone(self, phone: str) -> User | None:
        return self.db.query(User).filter(User.phone == phone, User.is_deleted.is_(False)).first()

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.query(User).filter(User.id == user_id, User.is_deleted.is_(False)).first()

    def update(self, user: User) -> User:
        self.db.commit()
        self.db.refresh(user)
        return user

    def change_password(self, user: User, new_password: str) -> None:
        user.hashed_password = get_password_hash(new_password)
        self.db.commit()
