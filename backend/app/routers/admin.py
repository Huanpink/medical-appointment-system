from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import cast, func, select, or_, String
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models import Appointment, AppointmentStatus, Doctor, DoctorSpecialty, Patient, Role, Service, Specialty, User
from app.schemas.admin import AdminDoctorUpdate, AdminPatientUpdate, AdminServiceCreate, AdminServiceUpdate

router = APIRouter(prefix="/api/admin", tags=["Admin"])


def admin_user(user=Depends(require_roles(Role.ADMIN))):
    return user


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), user=Depends(admin_user)):
    d = datetime.now().strftime('%Y-%m-%d')
    counts = {s.value: db.scalar(select(func.count()).select_from(Appointment).where(Appointment.appointment_date == d, Appointment.status == s.value)) or 0 for s in AppointmentStatus}
    return {"date": d, "total_today": sum(counts.values()), "waiting": counts[AppointmentStatus.WAITING.value], "completed": counts[AppointmentStatus.COMPLETED.value], "cancelled": counts[AppointmentStatus.CANCELLED.value], "no_show": counts[AppointmentStatus.NO_SHOW.value], "in_progress": counts[AppointmentStatus.IN_PROGRESS.value]}


@router.get("/patients")
def patients(q: str = Query(default=""), db: Session = Depends(get_db), user=Depends(admin_user)):
    needle = q.strip()
    stmt = select(Patient, User).join(User, Patient.user_id == User.id).order_by(User.full_name)
    if needle:
        p = f"%{needle}%"
        stmt = stmt.where(or_(User.full_name.ilike(p), User.phone.ilike(p), User.email.ilike(p), cast(User.id, String).ilike(p)))
    return [
        {"patient_id": p.id, "user_id": u.id, "patient_code": f"BN-{p.id:06d}", "full_name": u.full_name,
         "email": u.email, "phone": u.phone, "date_of_birth": p.date_of_birth, "gender": p.gender,
         "address": p.address, "emergency_contact": p.emergency_contact, "is_active": u.is_active}
        for p, u in db.execute(stmt).all()
    ]


@router.put("/patients/{patient_id}")
def update_patient(patient_id: int, data: AdminPatientUpdate, db: Session = Depends(get_db), user=Depends(admin_user)):
    p = db.get(Patient, patient_id)
    if not p:
        raise HTTPException(404, "Không tìm thấy bệnh nhân")
    u = db.get(User, p.user_id)
    email_owner = db.scalar(select(User).where(User.email == data.email.strip().lower(), User.id != u.id))
    if email_owner:
        raise HTTPException(409, "Email đã được sử dụng")
    u.full_name = data.full_name.strip()
    u.email = data.email.strip().lower()
    u.phone = data.phone.strip() if data.phone else None
    p.date_of_birth = data.date_of_birth
    p.gender = data.gender
    p.address = data.address
    p.emergency_contact = data.emergency_contact
    db.commit()
    return {"message": "Đã cập nhật hồ sơ bệnh nhân"}


@router.get("/doctors")
def doctors(db: Session = Depends(get_db), user=Depends(admin_user)):
    rows = db.execute(
        select(Doctor, User).join(User, Doctor.user_id == User.id).order_by(User.full_name)
    ).all()
    out = []
    for d, u in rows:
        sid = db.scalar(select(DoctorSpecialty.specialty_id).where(DoctorSpecialty.doctor_id == d.id).limit(1))
        sname = db.scalar(select(Specialty.name).where(Specialty.id == sid)) if sid else None
        out.append({"doctor_id": d.id, "user_id": u.id, "full_name": u.full_name, "phone": u.phone,
                    "email": u.email, "license_no": d.license_no, "bio": d.bio, "room": d.room,
                    "specialty_id": sid, "specialty_name": sname, "is_active": u.is_active})
    return out


@router.put("/doctors/{doctor_id}")
def update_doctor(doctor_id: int, data: AdminDoctorUpdate, db: Session = Depends(get_db), user=Depends(admin_user)):
    d = db.get(Doctor, doctor_id)
    if not d:
        raise HTTPException(404, "Không tìm thấy bác sĩ")
    u = db.get(User, d.user_id)
    other = db.scalar(select(Doctor).where(Doctor.license_no == data.license_no.strip(), Doctor.id != d.id))
    if other:
        raise HTTPException(409, "Số giấy phép đã tồn tại")
    if not db.get(Specialty, data.specialty_id):
        raise HTTPException(400, "Chuyên khoa không tồn tại")
    u.full_name = data.full_name.strip()
    u.phone = data.phone.strip() if data.phone else None
    d.license_no = data.license_no.strip()
    d.bio = data.bio.strip()
    d.room = data.room.strip()
    ds = db.scalars(select(DoctorSpecialty).where(DoctorSpecialty.doctor_id == d.id)).all()
    for item in ds:
        db.delete(item)
    db.flush()
    db.add(DoctorSpecialty(doctor_id=d.id, specialty_id=data.specialty_id))
    db.commit()
    return {"message": "Đã cập nhật thông tin bác sĩ"}


@router.get("/services")
def services(db: Session = Depends(get_db), user=Depends(admin_user)):
    rows = db.execute(select(Service, Specialty).join(Specialty, Service.specialty_id == Specialty.id).order_by(Specialty.name, Service.name)).all()
    return [{"id": s.id, "code": s.code, "name": s.name, "description": s.description, "price": s.price,
             "active": s.active, "specialty_id": sp.id, "specialty_name": sp.name} for s, sp in rows]


@router.post("/services")
def create_service(data: AdminServiceCreate, db: Session = Depends(get_db), user=Depends(admin_user)):
    if not db.get(Specialty, data.specialty_id):
        raise HTTPException(400, "Chuyên khoa không tồn tại")
    if db.scalar(select(Service).where(Service.code == data.code.strip())):
        raise HTTPException(409, "Mã dịch vụ đã tồn tại")
    s = Service(specialty_id=data.specialty_id, code=data.code.strip(), name=data.name.strip(), description=data.description.strip(), price=data.price, active=data.active)
    db.add(s); db.commit(); db.refresh(s)
    return {"id": s.id, "message": "Đã tạo dịch vụ"}


@router.put("/services/{service_id}")
def update_service(service_id: int, data: AdminServiceUpdate, db: Session = Depends(get_db), user=Depends(admin_user)):
    s = db.get(Service, service_id)
    if not s:
        raise HTTPException(404, "Không tìm thấy dịch vụ")
    if not db.get(Specialty, data.specialty_id):
        raise HTTPException(400, "Chuyên khoa không tồn tại")
    other = db.scalar(select(Service).where(Service.code == data.code.strip(), Service.id != s.id))
    if other:
        raise HTTPException(409, "Mã dịch vụ đã tồn tại")
    for k, v in data.model_dump().items():
        setattr(s, k, v.strip() if isinstance(v, str) else v)
    db.commit(); db.refresh(s)
    return {"message": "Đã cập nhật dịch vụ"}
