from pydantic import BaseModel, EmailStr, Field, field_validator
import re

from app.schemas.user import UserOut, UserOutNoImage


def validate_password_strength(value: str) -> str:
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not re.search(r"[A-Z]", value):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", value):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r"\d", value):
        raise ValueError("Password must contain at least one digit")
    if not re.search(r"[!@#$%^&*()_+\-=[\]{};':\",.<>/?]", value):
        raise ValueError("Password must contain at least one special character")
    return value


class UserRegister(BaseModel):
    email: EmailStr="user@gmail.com"
    full_name: str = Field(..., min_length=1)
    password: str = "NewTemp@123"
    phone: str = Field(..., min_length=10, max_length=10)
    address: str = Field(..., min_length=5)
    role: str = "Admin or Customer or Service Provider"

    @field_validator("phone")
    def phone_must_be_digits(cls, value: str) -> str:
        if not value.isdigit():
            raise ValueError("Phone number must contain only digits")
        if len(value) != 10:
            raise ValueError("Phone number must be exactly 10 digits")
        return value

    @field_validator("password")
    def validate_password(cls, value: str) -> str:
        return validate_password_strength(value)


class UserLogin(BaseModel):
    email: EmailStr="user@gmail.com"
    password: str = "NewTemp@123"


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOutNoImage


class ChangePassword(BaseModel):
    new_password: str

    @field_validator("new_password")
    def validate_new_password(cls, value: str) -> str:
        return validate_password_strength(value)


class ChangePasswordResponse(BaseModel):
    message: str = Field(..., json_schema_extra={"example": "Password changed successfully"})
