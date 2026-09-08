from pydantic import BaseModel

class ServiceOut(BaseModel):
    id: int
    code: str
    name: str
    description: str
    price: int
    specialty_id: int
    active: bool

class PaymentOut(BaseModel):
    id: int
    appointment_id: int
    service_id: int
    service_name: str
    amount: int
    method: str
    status: str
    reference: str
    qr_payload: str | None = None
    qr_image: str | None = None
    paid_at: str | None = None
