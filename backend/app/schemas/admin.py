from pydantic import BaseModel, Field

class AdminPatientUpdate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=160)
    phone: str | None = Field(default=None, max_length=30)
    date_of_birth: str | None = None
    gender: str | None = None
    address: str | None = None
    emergency_contact: str | None = None

class AdminSpecialtyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str = ""

class AdminDoctorCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=160)
    phone: str | None = Field(default=None, max_length=30)
    password: str = Field(min_length=6, max_length=120)
    license_no: str = Field(min_length=2, max_length=80)
    bio: str = ""
    room: str = Field(min_length=1, max_length=40)
    specialty_id: int

class AdminDoctorUpdate(BaseModel):
    email: str = Field(min_length=5, max_length=160)
    full_name: str = Field(min_length=2, max_length=120)
    phone: str | None = Field(default=None, max_length=30)
    license_no: str = Field(min_length=2, max_length=80)
    bio: str = ""
    room: str = Field(min_length=1, max_length=40)
    specialty_id: int

class AdminServiceCreate(BaseModel):
    specialty_id: int
    code: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=160)
    description: str = ""
    price: int = Field(ge=0)
    active: bool = True

class AdminServiceUpdate(AdminServiceCreate):
    pass

class ReceptionPatientCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    phone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=160)
    date_of_birth: str | None = None
    gender: str | None = None
    address: str | None = None
    emergency_contact: str | None = None


class AdminPasswordReset(BaseModel):
    password: str = Field(min_length=6, max_length=120)

class AdminUserUpdate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=160)
    phone: str | None = Field(default=None, max_length=30)
    is_active: bool = True
