from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import require_roles
from app.models import *
from app.schemas.appointment import WalkInIn, QueueOut

router = APIRouter(prefix="/api", tags=["Reception & Queue"])


def queue_payload(q):
    a = q.appointment
    return QueueOut(
        id=q.id,
        appointment_id=a.id,
        queue_no=q.queue_no,
        patient_name=a.patient.user.full_name,
        patient_phone=a.patient.user.phone,
        doctor_name=a.doctor.user.full_name,
        appointment_date=a.appointment_date,
        start_time=a.start_time,
        reason=a.reason,
        visit_type=a.visit_type,
        priority=q.priority,
        status=a.status,
        called_at=q.called_at.isoformat() if q.called_at else None,
    )


def next_queue_no(db, doctor_id, d=None):
    d = d or datetime.now().strftime("%Y-%m-%d")
    n = db.scalar(
        select(func.max(QueueEntry.queue_no)).join(Appointment).where(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == d,
        )
    ) or 0
    return n + 1


@router.get("/appointments")
def appointments(date: str | None = None, db: Session = Depends(get_db), user=Depends(require_roles(Role.RECEPTIONIST, Role.ADMIN))):
    d = date or datetime.now().strftime("%Y-%m-%d")
    rows = db.scalars(select(Appointment).where(Appointment.appointment_date == d).order_by(Appointment.start_time)).all()
    now = datetime.now()
    result = []
    for a in rows:
        scheduled = datetime.strptime(f"{a.appointment_date} {a.start_time}", "%Y-%m-%d %H:%M")
        late_minutes = max(0, int((now - scheduled).total_seconds() // 60)) if a.appointment_date == now.strftime("%Y-%m-%d") else 0
        result.append({
            "id": a.id,
            "appointment_code": f"AP-{a.id:06d}",
            "patient_id": a.patient_id,
            "patient_name": a.patient.user.full_name,
            "phone": a.patient.user.phone,
            "email": a.patient.user.email,
            "doctor_id": a.doctor_id,
            "doctor_name": a.doctor.user.full_name,
            "doctor_room": a.doctor.room,
            "date": a.appointment_date,
            "start_time": a.start_time,
            "end_time": a.end_time,
            "reason": a.reason,
            "status": a.status,
            "visit_type": a.visit_type,
            "service_name": a.service.name if a.service else None,
            "service_price": a.payment.amount if a.payment else (a.service.price if a.service else None),
            "payment_status": a.payment.status if a.payment else None,
            "payment_method": a.payment.method if a.payment else None,
            "checked_in_at": a.checked_in_at.isoformat() if a.checked_in_at else None,
            "late_minutes": late_minutes,
        })
    return result


@router.patch("/appointments/{appointment_id}/check-in")
def check_in(appointment_id: int, db: Session = Depends(get_db), user=Depends(require_roles(Role.RECEPTIONIST, Role.ADMIN))):
    a = db.get(Appointment, appointment_id)
    if not a:
        raise HTTPException(404, "Không tìm thấy lịch khám")
    if a.status != AppointmentStatus.CONFIRMED.value:
        raise HTTPException(400, "Lịch này không ở trạng thái có thể tiếp nhận")
    now = datetime.now()
    scheduled = datetime.strptime(f"{a.appointment_date} {a.start_time}", "%Y-%m-%d %H:%M")
    late_minutes = max(0, int((now - scheduled).total_seconds() // 60)) if a.appointment_date == now.strftime("%Y-%m-%d") else 0
    a.status = AppointmentStatus.CHECKED_IN.value
    a.checked_in_at = datetime.now(timezone.utc)
    q = QueueEntry(
        appointment_id=a.id,
        queue_no=next_queue_no(db, a.doctor_id),
        priority=1 if late_minutes <= 0 else 2,
    )
    db.add(q)
    a.status = AppointmentStatus.WAITING.value
    db.commit()
    return {"message": "Đã tiếp nhận bệnh nhân và đưa vào hàng chờ", "status": a.status, "queue_no": q.queue_no, "late_minutes": late_minutes}


@router.patch("/appointments/{appointment_id}/no-show")
def no_show(appointment_id: int, db: Session = Depends(get_db), user=Depends(require_roles(Role.RECEPTIONIST, Role.ADMIN))):
    a = db.get(Appointment, appointment_id)
    if not a:
        raise HTTPException(404, "Không tìm thấy lịch khám")
    if a.status != AppointmentStatus.CONFIRMED.value:
        raise HTTPException(400, "Lịch không còn ở trạng thái chờ bệnh nhân đến")
    now = datetime.now()
    scheduled = datetime.strptime(f"{a.appointment_date} {a.start_time}", "%Y-%m-%d %H:%M")
    if now < scheduled + timedelta(minutes=15):
        raise HTTPException(400, "Chỉ được đánh dấu không đến sau 15 phút kể từ giờ hẹn")
    a.status = AppointmentStatus.NO_SHOW.value
    if a.payment and a.payment.status in {PaymentStatus.PAID.value, PaymentStatus.PENDING.value}: a.payment.status = PaymentStatus.REFUND_PENDING.value
    db.commit()
    return {"message": "Đã đánh dấu bệnh nhân không đến khám"}


@router.post("/walk-ins", response_model=QueueOut)
def walk_in(data: WalkInIn, db: Session = Depends(get_db), user=Depends(require_roles(Role.RECEPTIONIST, Role.ADMIN))):
    p = db.get(Patient, data.patient_id)
    d = db.get(Doctor, data.doctor_id)
    if not p or not d:
        raise HTTPException(404, "Không tìm thấy bệnh nhân hoặc bác sĩ")
    today = datetime.now().strftime("%Y-%m-%d")
    now = datetime.now().strftime("%H:%M")
    a = Appointment(
        patient_id=p.id,
        doctor_id=d.id,
        appointment_date=today,
        start_time=now,
        end_time=now,
        reason=data.reason,
        status=AppointmentStatus.WAITING.value,
        visit_type=VisitType.WALK_IN.value,
        checked_in_at=datetime.now(timezone.utc),
    )
    db.add(a)
    db.flush()
    q = QueueEntry(appointment_id=a.id, queue_no=next_queue_no(db, d.id, today), priority=3)
    db.add(q)
    db.commit()
    db.refresh(q)
    return queue_payload(q)


@router.get("/queue", response_model=list[QueueOut])
def queue(doctorId: int | None = Query(default=None), db: Session = Depends(get_db), user=Depends(require_roles(Role.RECEPTIONIST, Role.ADMIN, Role.DOCTOR))):
    stmt = select(QueueEntry).join(Appointment).where(
        Appointment.status == AppointmentStatus.WAITING.value,
        Appointment.appointment_date == datetime.now().strftime("%Y-%m-%d"),
    ).order_by(QueueEntry.priority, QueueEntry.called_at.is_(None), QueueEntry.queue_no)
    if doctorId:
        stmt = stmt.where(Appointment.doctor_id == doctorId)
    return [queue_payload(q) for q in db.scalars(stmt).all()]


@router.post("/queue")
def add_to_queue(payload: dict = Body(...), db: Session = Depends(get_db), user=Depends(require_roles(Role.RECEPTIONIST, Role.ADMIN))):
    appointment_id = int(payload.get("appointment_id", 0))
    a = db.get(Appointment, appointment_id)
    if not a:
        raise HTTPException(404, "Không tìm thấy lịch khám")
    if a.status != AppointmentStatus.CHECKED_IN.value:
        raise HTTPException(400, "Lịch phải ở trạng thái đã tiếp nhận")
    a.status = AppointmentStatus.WAITING.value
    q = QueueEntry(appointment_id=a.id, queue_no=next_queue_no(db, a.doctor_id), priority=1)
    db.add(q)
    db.commit()
    return {"message": "Đã đưa vào hàng chờ"}


@router.patch("/queue/{queue_id}/call")
def call_queue(queue_id: int, db: Session = Depends(get_db), user=Depends(require_roles(Role.RECEPTIONIST, Role.ADMIN, Role.DOCTOR))):
    q = db.get(QueueEntry, queue_id)
    if not q or q.appointment.status != AppointmentStatus.WAITING.value:
        raise HTTPException(404, "Không có lượt đang chờ")
    q.called_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(q)
    return {"message": "Đã gọi bệnh nhân tiếp theo", "queue": queue_payload(q)}
