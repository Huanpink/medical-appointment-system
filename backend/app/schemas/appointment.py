from pydantic import BaseModel, Field

class AppointmentCreate(BaseModel):
    doctor_id: int
    service_id: int
    appointment_date: str
    start_time: str
    reason: str = Field(min_length=3, max_length=500)
    payment_method: str = Field(default="OFFLINE", pattern="^(OFFLINE|QR)$")

class AppointmentOut(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    doctor_name: str
    appointment_date: str
    start_time: str
    end_time: str
    reason: str
    status: str
    visit_type: str
    service_id: int | None = None
    service_name: str | None = None
    service_price: int | None = None
    payment_id: int | None = None
    payment_method: str | None = None
    payment_status: str | None = None
    payment_reference: str | None = None
    qr_payload: str | None = None
    qr_image: str | None = None
    specialty_name: str | None = None
    patient_name: str | None = None
    patient_phone: str | None = None
    diagnosis: str | None = None
    notes: str | None = None
    prescription: str | None = None

class RescheduleIn(BaseModel):
    appointment_date: str
    start_time: str

class MedicalResultIn(BaseModel):
    diagnosis: str = Field(min_length=2)
    notes: str = ""
    prescription: str = ""

class WalkInIn(BaseModel):
    patient_id: int
    doctor_id: int
    reason: str = Field(min_length=3)

class QueueOut(BaseModel):
    id: int
    appointment_id: int
    queue_no: int
    patient_name: str
    patient_phone: str | None = None
    doctor_name: str
    appointment_date: str
    start_time: str
    reason: str | None = None
    visit_type: str
    priority: int
    status: str
    called_at: str | None = None
