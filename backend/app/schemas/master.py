from pydantic import BaseModel, Field
from app.schemas.common import ORMModel

class SpecialtyOut(ORMModel):
    id: int
    name: str
    description: str

class DoctorOut(BaseModel):
    id: int
    full_name: str
    specialty_id: int | None = None
    specialty_name: str | None = None
    license_no: str
    bio: str
    room: str
    phone: str | None = None

class ProfileOut(BaseModel):
    id: int
    full_name: str
    email: str
    phone: str | None
    role: str
    patient_id: int | None = None
    patient_code: str | None = None
    date_of_birth: str | None = None
    gender: str | None = None
    address: str | None = None
    emergency_contact: str | None = None

class ScheduleIn(BaseModel):
    weekday: int = Field(ge=0, le=6)
    start_time: str
    end_time: str
    slot_minutes: int = Field(ge=10, le=240)

class ScheduleOut(ORMModel):
    id: int
    doctor_id: int
    weekday: int
    start_time: str
    end_time: str
    slot_minutes: int

class DayOffIn(BaseModel):
    date: str
    reason: str = ""

class DayOffOut(ORMModel):
    id: int
    doctor_id: int
    date: str
    reason: str
