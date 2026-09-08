from datetime import datetime
from enum import Enum
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class AppointmentStatus(str, Enum):
    CONFIRMED="CONFIRMED"; CHECKED_IN="CHECKED_IN"; WAITING="WAITING"; IN_PROGRESS="IN_PROGRESS"; COMPLETED="COMPLETED"; CANCELLED="CANCELLED"; NO_SHOW="NO_SHOW"
class VisitType(str, Enum):
    APPOINTMENT="APPOINTMENT"; WALK_IN="WALK_IN"

class Appointment(Base):
    __tablename__="appointments"
    __table_args__ = ()
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int]=mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), index=True)
    doctor_id: Mapped[int]=mapped_column(ForeignKey("doctors.id"), index=True)
    appointment_date: Mapped[str]=mapped_column(String(10), index=True)
    start_time: Mapped[str]=mapped_column(String(5))
    end_time: Mapped[str]=mapped_column(String(5))
    reason: Mapped[str]=mapped_column(String(500))
    service_id: Mapped[int|None]=mapped_column(ForeignKey("services.id", ondelete="RESTRICT"), nullable=True, index=True)
    status: Mapped[AppointmentStatus]=mapped_column(String(20), default=AppointmentStatus.CONFIRMED, index=True)
    visit_type: Mapped[VisitType]=mapped_column(String(20), default=VisitType.APPOINTMENT)
    checked_in_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=datetime.now)
    patient: Mapped["Patient"]=relationship(back_populates="appointments")
    doctor: Mapped["Doctor"]=relationship(back_populates="appointments")
    medical_result: Mapped["MedicalResult|None"]=relationship(back_populates="appointment", uselist=False, cascade="all, delete-orphan")
    queue_entry: Mapped["QueueEntry|None"]=relationship(back_populates="appointment", uselist=False, cascade="all, delete-orphan")
    service: Mapped["Service|None"] = relationship()
    payment: Mapped["Payment|None"] = relationship(back_populates="appointment", uselist=False, cascade="all, delete-orphan")

    @property
    def appointment_code(self) -> str:
        return f"AP-{self.id:06d}"

class PaymentStatus(str, Enum):
    UNPAID="UNPAID"
    PENDING="PENDING"
    PAID="PAID"
    REFUND_PENDING="REFUND_PENDING"
    REFUNDED="REFUNDED"

class PaymentMethod(str, Enum):
    OFFLINE="OFFLINE"
    QR="QR"

class Payment(Base):
    __tablename__="payments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    appointment_id: Mapped[int] = mapped_column(ForeignKey("appointments.id", ondelete="CASCADE"), unique=True, index=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id", ondelete="RESTRICT"))
    amount: Mapped[int] = mapped_column(Integer)
    method: Mapped[PaymentMethod] = mapped_column(String(20), default=PaymentMethod.OFFLINE)
    status: Mapped[PaymentStatus] = mapped_column(String(30), default=PaymentStatus.UNPAID)
    reference: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    qr_payload: Mapped[str|None] = mapped_column(Text, nullable=True)
    paid_at: Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)
    appointment: Mapped[Appointment] = relationship(back_populates="payment")
    service: Mapped["Service"] = relationship()

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
