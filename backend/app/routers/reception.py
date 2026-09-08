from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import require_roles
from app.models import *
from app.schemas.appointment import WalkInIn, QueueOut
from app.schemas.admin import ReceptionPatientCreate

router = APIRouter(prefix="/api", tags=["Reception & Queue"])


VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def _doctor_availability(db, doctor_id: int, now=None):
    now = now or datetime.now(VN_TZ)
    doctor = db.get(Doctor, doctor_id)
    if not doctor:
        return None
    if not doctor.user or not doctor.user.is_active:
        return {
            "doctor_id": doctor.id,
            "status": "INACTIVE",
            "label": "Không hoạt động",
            "working": False,
            "queue_count": 0,
            "current_patient": None,
        }

    today = now.strftime("%Y-%m-%d")
    if any(x.date == today for x in doctor.days_off):
        return {
            "doctor_id": doctor.id,
            "status": "DAY_OFF",
            "label": "Ngày nghỉ",
            "working": False,
            "queue_count": 0,
            "current_patient": None,
        }

    schedules = [x for x in doctor.schedules if x.weekday == now.weekday()]
    if not schedules:
        return {
            "doctor_id": doctor.id,
            "status": "NO_SCHEDULE",
            "label": "Chưa có lịch làm việc",
            "working": False,
            "queue_count": 0,
            "current_patient": None,
        }

    current_hm = now.strftime("%H:%M")
    active_shift = any(x.start_time <= current_hm < x.end_time for x in schedules)
    if not active_shift:
        return {
            "doctor_id": doctor.id,
            "status": "OFF_HOURS",
            "label": "Ngoài giờ làm việc",
            "working": False,
            "queue_count": 0,
            "current_patient": None,
        }

    waiting = db.scalars(select(QueueEntry).join(Appointment).where(
        Appointment.doctor_id == doctor.id,
        Appointment.appointment_date == today,
        Appointment.status == AppointmentStatus.WAITING.value,
    )).all()
    current = db.scalar(select(Appointment).where(
        Appointment.doctor_id == doctor.id,
        Appointment.appointment_date == today,
        Appointment.status == AppointmentStatus.IN_PROGRESS.value,
    ).order_by(Appointment.started_at.desc(), Appointment.id.desc()))
    current_name = current.patient.user.full_name if current and current.patient and current.patient.user else None
    if current:
        return {
            "doctor_id": doctor.id,
            "status": "BUSY",
            "label": "Đang khám",
            "working": True,
            "queue_count": len(waiting),
            "current_patient": current_name,
        }
    return {
        "doctor_id": doctor.id,
        "status": "AVAILABLE",
        "label": "Đang rảnh",
        "working": True,
        "queue_count": len(waiting),
        "current_patient": None,
    }


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


@router.get("/doctor-availability")
def doctor_availability(doctorId: int | None = Query(default=None), db: Session = Depends(get_db), user=Depends(require_roles(Role.RECEPTIONIST, Role.ADMIN))):
    now = datetime.now(VN_TZ)
    stmt = select(Doctor)
    if doctorId:
        stmt = stmt.where(Doctor.id == doctorId)
    doctors = db.scalars(stmt.order_by(Doctor.id)).all()
    return [_doctor_availability(db, d.id, now) for d in doctors]


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
            "appointment_code": a.appointment_code,
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
    refund_pending = False
    if a.payment:
        if a.payment.status == PaymentStatus.PAID.value:
            a.payment.status = PaymentStatus.REFUND_PENDING.value
            refund_pending = True
        elif a.payment.status == PaymentStatus.PENDING.value:
            a.payment.status = PaymentStatus.UNPAID.value
            a.payment.qr_payload = None
    db.commit()
    return {
        "message": "Đã đánh dấu bệnh nhân không đến khám",
        "refund_pending": refund_pending,
        "payment_status": a.payment.status if a.payment else None
    }


@router.get("/refund-requests")
def refund_requests(db: Session = Depends(get_db), user=Depends(require_roles(Role.RECEPTIONIST, Role.ADMIN))):
    rows = db.scalars(
        select(Appointment).join(Payment).where(Payment.status == PaymentStatus.REFUND_PENDING.value)
        .order_by(Appointment.appointment_date.desc(), Appointment.start_time.desc())
    ).all()
    return [{
        "appointment_id": a.id,
        "appointment_code": a.appointment_code,
        "patient_id": a.patient_id,
        "patient_code": a.patient.patient_code,
        "patient_name": a.patient.user.full_name,
        "phone": a.patient.user.phone,
        "email": a.patient.user.email,
        "appointment_date": a.appointment_date,
        "start_time": a.start_time,
        "doctor_name": a.doctor.user.full_name,
        "service_name": a.service.name if a.service else None,
        "amount": a.payment.amount if a.payment else 0,
        "payment_method": a.payment.method if a.payment else None,
        "payment_reference": a.payment.reference if a.payment else None,
        "appointment_status": a.status,
        "payment_status": a.payment.status if a.payment else None,
        "checked_in_at": a.checked_in_at.isoformat() if a.checked_in_at else None,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    } for a in rows]


@router.post("/reception-patients")
def create_reception_patient(data: ReceptionPatientCreate, db: Session = Depends(get_db), user=Depends(require_roles(Role.RECEPTIONIST, Role.ADMIN))):
    from uuid import uuid4
    full_name = data.full_name.strip()
    email = (data.email or "").strip().lower()
    if email:
        if db.scalar(select(User).where(User.email == email)):
            raise HTTPException(409, "Email đã được sử dụng")
    else:
        # Walk-in patients do not need a login email. Generate a stable internal
        # address so the existing User/Patient relationship remains intact.
        email = f"patient-{uuid4().hex[:12]}@internal.medschedule.local"
    u = User(
        full_name=full_name,
        email=email,
        phone=data.phone.strip() if data.phone else None,
        password_hash=__import__('app.core.security', fromlist=['hash_password']).hash_password(uuid4().hex),
        role=Role.PATIENT,
    )
    db.add(u)
    db.flush()
    p = Patient(user_id=u.id, date_of_birth=data.date_of_birth, gender=data.gender, address=data.address, emergency_contact=data.emergency_contact)
    db.add(p)
    db.flush()
    db.commit()
    return {
        "patient_id": p.id,
        "patient_code": p.patient_code,
        "user_id": u.id,
        "full_name": u.full_name,
        "phone": u.phone,
        "email": data.email.strip().lower() if data.email else None,
    }


@router.post("/walk-ins", response_model=QueueOut)
def walk_in(data: WalkInIn, db: Session = Depends(get_db), user=Depends(require_roles(Role.RECEPTIONIST, Role.ADMIN))):
    p = db.get(Patient, data.patient_id)
    d = db.get(Doctor, data.doctor_id)
    if not p or not d:
        raise HTTPException(404, "Không tìm thấy bệnh nhân hoặc bác sĩ")
    availability = _doctor_availability(db, d.id)
    if not availability:
        raise HTTPException(404, "Không tìm thấy trạng thái bác sĩ")
    if availability["status"] in {"INACTIVE", "DAY_OFF", "NO_SCHEDULE", "OFF_HOURS"}:
        raise HTTPException(400, f"Không thể tiếp nhận: bác sĩ hiện ở trạng thái {availability['label'].lower()}")
    today = datetime.now(VN_TZ).strftime("%Y-%m-%d")
    now = datetime.now(VN_TZ).strftime("%H:%M")
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
