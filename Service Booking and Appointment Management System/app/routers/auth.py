from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.oauth2 import get_current_user
from app.database import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AuthResponse, ChangePassword, ChangePasswordResponse, RefreshTokenRequest, Token, UserLogin, UserRegister
from app.schemas.user import UserOut, UserOutNoImage, UserUpdate
from app.services.auth_service import AuthService
from app.models.user import User

router = APIRouter()


@router.post("/register", response_model=UserOutNoImage)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    service = AuthService(db)
    user = service.register(user_in)
    return user


@router.post("/login", response_model=AuthResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    service = AuthService(db)
    user, access_token, refresh_token = service.login(credentials)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user,
    }


@router.post("/refresh", response_model=Token)
def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    access_token = service.refresh_access_token(payload.refresh_token)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/profile", response_model=UserOutNoImage)
def profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/profile", response_model=UserOutNoImage)
def update_profile(payload: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = UserRepository(db)
    updated = False

    if payload.email is not None:
        existing_email = repo.get_by_email(payload.email)
        if existing_email and existing_email.id != current_user.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already registered")
        current_user.email = payload.email
        updated = True

    if payload.full_name is not None:
        current_user.full_name = payload.full_name.strip()
        updated = True

    if payload.phone is not None:
        existing_phone = repo.get_by_phone(payload.phone)
        if existing_phone and existing_phone.id != current_user.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number already registered")
        current_user.phone = payload.phone
        updated = True

    if payload.address is not None:
        current_user.address = payload.address.strip()
        updated = True

    if not updated:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid profile fields provided to update")

    db.commit()
    db.refresh(current_user)
    return current_user


@router.put( "/change-password",response_model=ChangePasswordResponse,
            description="New password only. Requirements:\n\n"
        "- At least 8 characters long\n"
        "- At least one uppercase letter\n"
        "- At least one lowercase letter\n"
        "- At least one digit\n"
        "- At least one special character\n")
def change_password(
    payload: ChangePassword = Body(...,examples={"new_password": "NewTemp@123"}),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    service.change_password(current_user, payload.new_password)
    return {"message": "Password changed successfully"}
