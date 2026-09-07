from pydantic import BaseModel, Field, field_validator
from app.models.user import Role
from app.schemas.common import ORMModel

def _validate_email(value: str) -> str:
    value = value.strip().lower()
    if len(value) > 160 or "@" not in value:
        raise ValueError("Email không hợp lệ")
    local, domain = value.rsplit("@", 1)
    if not local or not domain or "." not in domain:
        raise ValueError("Email không hợp lệ")
    return value

class RegisterIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: str
    phone: str = Field(min_length=8, max_length=30)
    password: str = Field(min_length=6, max_length=100)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _validate_email(value)

class LoginIn(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _validate_email(value)

class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6, max_length=100)

class UserOut(ORMModel):
    id: int
    full_name: str
    email: str
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
