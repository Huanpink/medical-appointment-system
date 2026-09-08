from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Patient(Base):
    __tablename__ = "patients"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    date_of_birth: Mapped[str | None] = mapped_column(String(20), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    emergency_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)

    @property
    def patient_code(self) -> str:
        """Human-friendly patient code derived from the database id.

        The database id is auto-incremented, so every newly created patient
        automatically receives a stable code without requiring a manual field.
        """
        return f"BN-{self.id:06d}"

    user: Mapped["User"] = relationship(back_populates="patient")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="patient")

class Specialty(Base):
    __tablename__ = "specialties"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    doctors: Mapped[list["DoctorSpecialty"]] = relationship(back_populates="specialty")
    services: Mapped[list["Service"]] = relationship(back_populates="specialty")

class Service(Base):
    __tablename__ = "services"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    specialty_id: Mapped[int] = mapped_column(ForeignKey("specialties.id", ondelete="RESTRICT"), index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text, default="")
    price: Mapped[int] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    specialty: Mapped["Specialty"] = relationship(back_populates="services")

class Doctor(Base):
    __tablename__ = "doctors"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    license_no: Mapped[str] = mapped_column(String(80), unique=True)
    bio: Mapped[str] = mapped_column(Text, default="")
    room: Mapped[str] = mapped_column(String(40), default="101")
    user: Mapped["User"] = relationship(back_populates="doctor")
    specialties: Mapped[list["DoctorSpecialty"]] = relationship(back_populates="doctor", cascade="all, delete-orphan")
    schedules: Mapped[list["DoctorSchedule"]] = relationship(back_populates="doctor", cascade="all, delete-orphan")
    days_off: Mapped[list["DoctorDayOff"]] = relationship(back_populates="doctor", cascade="all, delete-orphan")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="doctor")

class DoctorSpecialty(Base):
    __tablename__ = "doctor_specialties"
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id", ondelete="CASCADE"), primary_key=True)
    specialty_id: Mapped[int] = mapped_column(ForeignKey("specialties.id", ondelete="CASCADE"), primary_key=True)
    doctor: Mapped[Doctor] = relationship(back_populates="specialties")
    specialty: Mapped[Specialty] = relationship(back_populates="doctors")

class DoctorSchedule(Base):
    __tablename__ = "doctor_schedules"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id", ondelete="CASCADE"), index=True)
    weekday: Mapped[int] = mapped_column(Integer)  # 0 Monday .. 6 Sunday
    start_time: Mapped[str] = mapped_column(String(5))
    end_time: Mapped[str] = mapped_column(String(5))
    slot_minutes: Mapped[int] = mapped_column(Integer, default=30)
    doctor: Mapped[Doctor] = relationship(back_populates="schedules")

class DoctorDayOff(Base):
    __tablename__ = "doctor_days_off"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id", ondelete="CASCADE"), index=True)
    date: Mapped[str] = mapped_column(String(10), index=True)
    reason: Mapped[str] = mapped_column(String(255), default="")
    doctor: Mapped[Doctor] = relationship(back_populates="days_off")
