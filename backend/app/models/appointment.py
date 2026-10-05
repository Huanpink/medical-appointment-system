from datetime import datetime
from enum import Enum
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class AppointmentStatus(str, Enum):
    CONFIRMED="CONFIRMED"; CHECKED_IN="CHECKED_IN"; WAITING="WAITING"; IN_PROGRESS="IN_PROGRESS"; COMPLETED="COMPLETED"; CANCELLED="CANCELLED"; NO_SHOW="NO_SHOW"
class VisitType(str, Enum):
    APPOINTMENT="APPOINTMENT"; WALK_IN="WALK_IN"

class Appointment(Base):
    __tablename__="appointments"
    __table_args__=(UniqueConstraint("doctor_id","appointment_date","start_time", name="uq_doctor_slot"),)
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int]=mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), index=True)
    doctor_id: Mapped[int]=mapped_column(ForeignKey("doctors.id"), index=True)
    appointment_date: Mapped[str]=mapped_column(String(10), index=True)
    start_time: Mapped[str]=mapped_column(String(5))
    end_time: Mapped[str]=mapped_column(String(5))
    reason: Mapped[str]=mapped_column(String(500))
    status: Mapped[AppointmentStatus]=mapped_column(String(20), default=AppointmentStatus.CONFIRMED, index=True)
    visit_type: Mapped[VisitType]=mapped_column(String(20), default=VisitType.APPOINTMENT)
    checked_in_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    patient: Mapped["Patient"]=relationship(back_populates="appointments")
    doctor: Mapped["Doctor"]=relationship(back_populates="appointments")
    medical_result: Mapped["MedicalResult|None"]=relationship(back_populates="appointment", uselist=False, cascade="all, delete-orphan")
    queue_entry: Mapped["QueueEntry|None"]=relationship(back_populates="appointment", uselist=False, cascade="all, delete-orphan")

class MedicalResult(Base):
    __tablename__="medical_results"
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    appointment_id: Mapped[int]=mapped_column(ForeignKey("appointments.id", ondelete="CASCADE"), unique=True)
    diagnosis: Mapped[str]=mapped_column(Text)
    notes: Mapped[str]=mapped_column(Text, default="")
    prescription: Mapped[str]=mapped_column(Text, default="")
    appointment: Mapped[Appointment]=relationship(back_populates="medical_result")

class QueueEntry(Base):
    __tablename__="queue_entries"
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    appointment_id: Mapped[int]=mapped_column(ForeignKey("appointments.id", ondelete="CASCADE"), unique=True)
    queue_no: Mapped[int]=mapped_column(Integer)
    priority: Mapped[int]=mapped_column(Integer, default=1)
    called_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True), nullable=True)
    appointment: Mapped[Appointment]=relationship(back_populates="queue_entry")
