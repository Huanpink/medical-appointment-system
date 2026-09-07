from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, EmailStr, Field, TypeAdapter

from app.models.user import Role
from app.schemas.common import ORMModel

_EMAIL_ADAPTER = TypeAdapter(EmailStr)


def _validate_email(value: Any) -> str:
    """Validate normal emails while allowing local-only demo domains such as *.local."""
    if not isinstance(value, str):
        raise ValueError("Email không hợp lệ")
    value = value.strip().lower()
    if "@" not in value or value.startswith("@") or value.endswith("@"):
        raise ValueError("Email không hợp lệ")
    domain = value.rsplit("@", 1)[1]
    if domain.endswith(".local"):
        return value
    return str(_EMAIL_ADAPTER.validate_python(value))


LocalEmail = Annotated[str, BeforeValidator(_validate_email)]


class RegisterIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: LocalEmail
    phone: str = Field(min_length=8, max_length=30)
    password: str = Field(min_length=6, max_length=100)


class LoginIn(BaseModel):
    email: LocalEmail
    password: str = Field(min_length=1, max_length=100)


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=100)
    new_password: str = Field(min_length=6, max_length=100)


class UserOut(ORMModel):
    id: int
    full_name: str
    email: LocalEmail
    phone: str | None
    role: Role
    patient_id: int | None = None
    doctor_id: int | None = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class PatientProfile(BaseModel):
    date_of_birth: str | None = None
    gender: str | None = None
    address: str | None = None
    emergency_contact: str | None = None
