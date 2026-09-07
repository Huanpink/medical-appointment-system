from pydantic import BaseModel, EmailStr, Field
from app.models.user import Role
from app.schemas.common import ORMModel
class RegisterIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str = Field(min_length=8, max_length=30)
    password: str = Field(min_length=6, max_length=100)
class LoginIn(BaseModel):
    email: EmailStr
    password: str
class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6, max_length=100)
class UserOut(ORMModel):
    id: int; full_name: str; email: EmailStr; phone: str|None; role: Role; patient_id: int|None=None; doctor_id: int|None=None
class TokenOut(BaseModel): access_token: str; token_type: str = "bearer"; user: UserOut
class PatientProfile(BaseModel):
    date_of_birth: str|None=None; gender: str|None=None; address: str|None=None; emergency_contact: str|None=None
