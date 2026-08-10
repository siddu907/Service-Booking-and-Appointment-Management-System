from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: str
    phone: str | None = None
    address: str | None = None
    profile_image: str | None = None
    is_active: bool


class UserOutNoImage(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: str
    phone: str | None = None
    address: str | None = None
    is_active: bool


class UserUpdate(BaseModel):
    email: EmailStr | None = Field(None, example="user@gmail.com")
    full_name: str | None = None
    phone: str | None = None
    address: str | None = None

    @field_validator("full_name")
    def validate_full_name(cls, value: str) -> str:
        if value is not None and not value.strip():
            raise ValueError("Full name must not be blank")
        return value

    @field_validator("phone")
    def validate_phone(cls, value: str) -> str:
        if value is not None:
            if not value.isdigit() or len(value) != 10:
                raise ValueError("Phone number must be exactly 10 digits and contain only numbers")
        return value

    @field_validator("address")
    def validate_address(cls, value: str) -> str:
        if value is not None and len(value.strip()) < 5:
            raise ValueError("Address must be at least 5 characters")
        return value
