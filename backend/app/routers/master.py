from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import cast, or_, select, String
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models import User, Patient, Doctor, Specialty, Service, DoctorSpecialty, Role
from app.schemas.auth import PatientProfile
from app.schemas.master import SpecialtyOut, DoctorOut, ProfileOut
from app.schemas.payment import ServiceOut

router=APIRouter(prefix="/api",tags=["Master Data"])

@router.get("/specialties",response_model=list[SpecialtyOut])
def specialties(db:Session=Depends(get_db)):
    return db.scalars(select(Specialty).order_by(Specialty.name)).all()

@router.get("/services", response_model=list[ServiceOut])
def services(specialtyId: int | None = Query(default=None), db: Session = Depends(get_db)):
    stmt=select(Service).where(Service.active == True).order_by(Service.price, Service.name)
    if specialtyId: stmt=stmt.where(Service.specialty_id == specialtyId)
    return db.scalars(stmt).all()

@router.get("/doctors",response_model=list[DoctorOut])
def doctors(specialtyId:int|None=Query(default=None), db:Session=Depends(get_db)):
    stmt=select(Doctor,User.full_name,DoctorSpecialty.specialty_id,Specialty.name).join(User,Doctor.user_id==User.id).outerjoin(DoctorSpecialty,DoctorSpecialty.doctor_id==Doctor.id).outerjoin(Specialty,Specialty.id==DoctorSpecialty.specialty_id)
    if specialtyId: stmt=stmt.where(DoctorSpecialty.specialty_id==specialtyId)
    rows=db.execute(stmt.order_by(User.full_name)).all()
    seen=set(); out=[]
    for d,name,sid,sname in rows:
        if d.id in seen: continue
        seen.add(d.id); out.append(DoctorOut(id=d.id,full_name=name,specialty_id=sid,specialty_name=sname,license_no=d.license_no,bio=d.bio,room=d.room))
    return out

@router.get("/doctors/{doctor_id}",response_model=DoctorOut)
def doctor(doctor_id:int,db:Session=Depends(get_db)):
    row=db.execute(select(Doctor,User.full_name,DoctorSpecialty.specialty_id,Specialty.name).join(User,Doctor.user_id==User.id).outerjoin(DoctorSpecialty,DoctorSpecialty.doctor_id==Doctor.id).outerjoin(Specialty,Specialty.id==DoctorSpecialty.specialty_id).where(Doctor.id==doctor_id)).first()
    if not row: raise HTTPException(404,"Không tìm thấy bác sĩ")
    d,name,sid,sname=row
    return DoctorOut(id=d.id,full_name=name,specialty_id=sid,specialty_name=sname,license_no=d.license_no,bio=d.bio,room=d.room)

# Static path must be declared before /patients/{patient_id}.
@router.get("/patients/search")
def search_patients(q:str=Query(min_length=1),db:Session=Depends(get_db),user:User=Depends(require_roles(Role.RECEPTIONIST,Role.ADMIN))):
    needle=f"%{q.strip()}%"
    stmt=select(Patient,User).join(User,Patient.user_id==User.id).where(
        or_(
            User.full_name.ilike(needle),
            User.phone.ilike(needle),
            User.email.ilike(needle),
            cast(Patient.id, String).ilike(needle),
            ("BN-" + cast(Patient.id, String)).ilike(needle),
        )
    )
    return [{"id":p.id,"full_name":u.full_name,"phone":u.phone,"email":u.email,"patient_code":p.patient_code} for p,u in db.execute(stmt).all()]

@router.get("/patients/{patient_id}",response_model=ProfileOut)
def patient_profile(patient_id:int,db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    p=db.get(Patient,patient_id)
    if not p: raise HTTPException(404,"Không tìm thấy bệnh nhân")
    if user.role==Role.PATIENT and p.user_id!=user.id: raise HTTPException(403,"Không có quyền")
    u=db.get(User,p.user_id)
    return ProfileOut(id=u.id,full_name=u.full_name,email=u.email,phone=u.phone,role=u.role.value,patient_id=p.id,patient_code=p.patient_code,date_of_birth=p.date_of_birth,gender=p.gender,address=p.address,emergency_contact=p.emergency_contact)

@router.put("/patients/{patient_id}")
def update_patient(patient_id:int,data:PatientProfile,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    p=db.get(Patient,patient_id)
    if not p: raise HTTPException(404,"Không tìm thấy bệnh nhân")
    if user.role==Role.PATIENT and p.user_id!=user.id: raise HTTPException(403,"Không có quyền")
    for k,v in data.model_dump(exclude_unset=True).items(): setattr(p,k,v)
    db.commit()
    return {"message":"Cập nhật hồ sơ thành công"}
