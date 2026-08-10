from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.constants import USER_ROLES
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserRegister, UserLogin
from app.models.user import User


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = UserRepository(db)

    def register(self, user_in: UserRegister) -> User:
        if user_in.role not in USER_ROLES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user role")
        if self.repo.get_by_email(user_in.email):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
        if self.repo.get_by_phone(user_in.phone):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number already registered")
        user = self.repo.create(
            user_in.email,
            user_in.full_name,
            user_in.password,
            user_in.role,
            user_in.phone,
            user_in.address,
        )
        return user

    def login(self, credentials: UserLogin) -> tuple[User, str, str]:
        user = self.repo.get_by_email(str(credentials.email))
        if not user or not verify_password(credentials.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        access_token = create_access_token(str(user.id), user.role)
        refresh_token = create_refresh_token(str(user.id), user.role)
        return user, access_token, refresh_token

    def refresh_access_token(self, refresh_token: str) -> str:
        from app.core.security import decode_token

        try:
            payload = decode_token(refresh_token)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        user = self.repo.get_by_id(int(user_id))
        if not user or user.is_deleted:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        return create_access_token(str(user.id), user.role)

    def change_password(self, user: User, new_password: str) -> None:
        if verify_password(new_password, user.hashed_password):
            raise HTTPException(status_code=400, detail="New password must be different from the old password")
        self.repo.change_password(user, new_password)
