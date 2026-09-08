from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import cast, func, select, or_, String
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models import Appointment, AppointmentStatus, Doctor, DoctorSpecialty, Patient, Role, Service, Specialty, User
from app.schemas.admin import AdminDoctorCreate, AdminDoctorUpdate, AdminPatientUpdate, AdminServiceCreate, AdminServiceUpdate, AdminSpecialtyCreate, AdminPasswordReset, AdminUserUpdate
from app.core.security import hash_password

router = APIRouter(prefix="/api/admin", tags=["Admin"])


def admin_user(user=Depends(require_roles(Role.ADMIN))):
    return user


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), user=Depends(admin_user)):
    d = datetime.now().strftime('%Y-%m-%d')
    counts = {s.value: db.scalar(select(func.count()).select_from(Appointment).where(Appointment.appointment_date == d, Appointment.status == s.value)) or 0 for s in AppointmentStatus}
    return {"date": d, "total_today": sum(counts.values()), "waiting": counts[AppointmentStatus.WAITING.value], "completed": counts[AppointmentStatus.COMPLETED.value], "cancelled": counts[AppointmentStatus.CANCELLED.value], "no_show": counts[AppointmentStatus.NO_SHOW.value], "in_progress": counts[AppointmentStatus.IN_PROGRESS.value]}


@router.get("/users")
def users(q: str = Query(default=""), group: str = Query(default="all"), db: Session = Depends(get_db), user=Depends(admin_user)):
    needle = q.strip()
    stmt = select(User)
    if group == "staff":
        stmt = stmt.where(User.role.in_([Role.DOCTOR, Role.RECEPTIONIST]))
    elif group == "customers":
        stmt = stmt.where(User.role == Role.PATIENT)
    elif group == "admin":
        stmt = stmt.where(User.role == Role.ADMIN)
    stmt = stmt.order_by(User.role, User.full_name)
    if needle:
        p = f"%{needle}%"
        conditions = [User.full_name.ilike(p), User.email.ilike(p), User.phone.ilike(p), cast(User.id, String).ilike(p)]
        patient_ids = [x[0] for x in db.execute(select(Patient.user_id).where(cast(Patient.id, String).ilike(p))).all()]
        if patient_ids:
            conditions.append(User.id.in_(patient_ids))
        stmt = stmt.where(or_(*conditions))
    rows = db.scalars(stmt).all()
    out=[]
    for u in rows:
        patient = db.scalar(select(Patient).where(Patient.user_id == u.id))
        doctor = db.scalar(select(Doctor).where(Doctor.user_id == u.id))
        role = u.role.value if hasattr(u.role,'value') else str(u.role)
        out.append({"id":u.id,"user_code":f"USER-{u.id:06d}","full_name":u.full_name,"email":u.email,"phone":u.phone,"role":role,"is_active":u.is_active,"patient_id":patient.id if patient else None,"patient_code":patient.patient_code if patient else None,"doctor_id":doctor.id if doctor else None})
    return out

@router.get("/accounts")
def accounts(q: str = Query(default=""), group: str = Query(default="all"), db: Session = Depends(get_db), user=Depends(admin_user)):
    needle = q.strip()
    stmt = select(User)
    if group == "staff":
        stmt = stmt.where(User.role.in_([Role.DOCTOR, Role.RECEPTIONIST]))
    elif group == "customers":
        stmt = stmt.where(User.role == Role.PATIENT)
    elif group == "admin":
        stmt = stmt.where(User.role == Role.ADMIN)
    if needle:
        ptn = f"%{needle}%"
        user_ids = list(db.scalars(select(Patient.user_id).where(Patient.patient_code.ilike(ptn))).all())
        conditions = [User.full_name.ilike(ptn), User.email.ilike(ptn), User.phone.ilike(ptn), cast(User.id, String).ilike(ptn)]
        if user_ids:
            conditions.append(User.id.in_(user_ids))
        stmt = stmt.where(or_(*conditions))
    rows = db.scalars(stmt.order_by(User.role, User.full_name)).all()
    out = []
    for u in rows:
        patient = db.scalar(select(Patient).where(Patient.user_id == u.id))
        doctor = db.scalar(select(Doctor).where(Doctor.user_id == u.id))
        role = u.role.value if hasattr(u.role, 'value') else str(u.role)
        out.append({"id": u.id, "user_code": f"USER-{u.id:06d}", "full_name": u.full_name, "email": u.email,
                    "phone": u.phone, "role": role, "is_active": u.is_active,
                    "patient_id": patient.id if patient else None, "patient_code": patient.patient_code if patient else None,
                    "doctor_id": doctor.id if doctor else None})
    return out


@router.put("/users/{user_id}")
def update_user(user_id: int, data: AdminUserUpdate, db: Session = Depends(get_db), user=Depends(admin_user)):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(404, "Không tìm thấy tài khoản")
    email = data.email.strip().lower()
    other = db.scalar(select(User).where(User.email == email, User.id != user_id))
    if other:
        raise HTTPException(409, "Email đã được sử dụng")
    if target.id == user.id and not data.is_active:
        raise HTTPException(400, "Không thể tự khóa tài khoản đang đăng nhập")
    target.full_name = data.full_name.strip()
    target.email = email
    target.phone = data.phone.strip() if data.phone else None
    target.is_active = data.is_active
    db.commit()
    db.refresh(target)
    return {"message":"Đã cập nhật tài khoản", "id": target.id, "user_code": f"USER-{target.id:06d}", "full_name": target.full_name, "email": target.email, "phone": target.phone, "role": target.role.value if hasattr(target.role, "value") else str(target.role), "is_active": target.is_active}


@router.post("/users/{user_id}/reset-password")
def reset_user_password(user_id: int, data: AdminPasswordReset, db: Session = Depends(get_db), user=Depends(admin_user)):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(404, "Không tìm thấy tài khoản")
    target.password_hash = hash_password(data.password)
    db.commit()
    return {"message":"Đã đặt lại mật khẩu"}


@router.get("/patients")
def patients(q: str = Query(default=""), db: Session = Depends(get_db), user=Depends(admin_user)):
    needle = q.strip()
    stmt = select(Patient, User).join(User, Patient.user_id == User.id).order_by(User.full_name)
    if needle:
        p = f"%{needle}%"
        stmt = stmt.where(or_(User.full_name.ilike(p), User.phone.ilike(p), User.email.ilike(p), cast(User.id, String).ilike(p)))
    return [
        {"patient_id": p.id, "user_id": u.id, "patient_code": p.patient_code, "full_name": u.full_name,
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


@router.get("/specialties")
def specialties(db: Session = Depends(get_db), user=Depends(admin_user)):
    rows = db.scalars(select(Specialty).order_by(Specialty.name)).all()
    return [{"id": s.id, "name": s.name, "description": s.description} for s in rows]


@router.post("/specialties")
def create_specialty(data: AdminSpecialtyCreate, db: Session = Depends(get_db), user=Depends(admin_user)):
    name = data.name.strip()
    if db.scalar(select(Specialty).where(func.lower(Specialty.name) == name.lower())):
        raise HTTPException(409, "Chuyên khoa đã tồn tại")
    s = Specialty(name=name, description=data.description.strip())
    db.add(s); db.commit(); db.refresh(s)
    return {"id": s.id, "name": s.name, "description": s.description, "message": "Đã thêm chuyên khoa"}


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


@router.post("/doctors")
def create_doctor(data: AdminDoctorCreate, db: Session = Depends(get_db), user=Depends(admin_user)):
    email = data.email.strip().lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "Email tài khoản bác sĩ đã tồn tại")
    if db.scalar(select(Doctor).where(Doctor.license_no == data.license_no.strip())):
        raise HTTPException(409, "Số giấy phép đã tồn tại")
    if not db.get(Specialty, data.specialty_id):
        raise HTTPException(400, "Chuyên khoa không tồn tại")
    u = User(full_name=data.full_name.strip(), email=email, phone=data.phone.strip() if data.phone else None, password_hash=hash_password(data.password), role=Role.DOCTOR, is_active=True)
    db.add(u); db.flush()
    d = Doctor(user_id=u.id, license_no=data.license_no.strip(), bio=data.bio.strip(), room=data.room.strip())
    db.add(d); db.flush()
    db.add(DoctorSpecialty(doctor_id=d.id, specialty_id=data.specialty_id))
    db.commit(); db.refresh(d)
    return {"doctor_id": d.id, "user_id": u.id, "full_name": u.full_name, "email": u.email, "message": "Đã thêm bác sĩ và cấp tài khoản đăng nhập"}


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
    email = data.email.strip().lower()
    email_owner = db.scalar(select(User).where(User.email == email, User.id != u.id))
    if email_owner:
        raise HTTPException(409, "Email đã được sử dụng")
    u.full_name = data.full_name.strip()
    u.email = email
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
    db.refresh(u)
    db.refresh(d)
    return {
        "message": "Đã cập nhật thông tin bác sĩ",
        "login_email": u.email,
        "doctor_id": d.id,
        "user_id": u.id,
        "full_name": u.full_name,
        "email": u.email,
        "phone": u.phone,
        "license_no": d.license_no,
        "room": d.room,
        "specialty_id": data.specialty_id,
    }


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


@router.get("/accounts-v2")
def accounts_v2(q: str = Query(default=""), group: str = Query(default="all"), db: Session = Depends(get_db), user=Depends(admin_user)):
    return accounts(q=q, group=group, db=db, user=user)
