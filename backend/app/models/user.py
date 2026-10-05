from enum import Enum
from sqlalchemy import Boolean, Enum as SAEnum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Role(str, Enum):
    PATIENT = "PATIENT"
    RECEPTIONIST = "RECEPTIONIST"
    DOCTOR = "DOCTOR"
    ADMIN = "ADMIN"

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(SAEnum(Role, native_enum=False), default=Role.PATIENT)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    @property
    def patient_id(self):
        return self.patient.id if self.patient else None
    @property
    def doctor_id(self):
        return self.doctor.id if self.doctor else None
    patient: Mapped["Patient"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    doctor: Mapped["Doctor"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
