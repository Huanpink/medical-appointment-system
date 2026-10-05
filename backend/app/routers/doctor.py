from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import require_roles
from app.models import *
from app.schemas.master import ScheduleIn,ScheduleOut,DayOffIn,DayOffOut
from app.schemas.appointment import AppointmentOut,MedicalResultIn

router=APIRouter(prefix="/api",tags=["Doctor & Schedule"])
@router.get("/doctors/{doctor_id}/schedules",response_model=list[ScheduleOut])
def schedules(doctor_id:int,db:Session=Depends(get_db)): return db.scalars(select(DoctorSchedule).where(DoctorSchedule.doctor_id==doctor_id).order_by(DoctorSchedule.weekday)).all()
@router.post("/doctors/{doctor_id}/schedules",response_model=ScheduleOut)
def add_schedule(doctor_id:int,data:ScheduleIn,db:Session=Depends(get_db),user=Depends(require_roles(Role.DOCTOR,Role.ADMIN))):
    if user.role==Role.DOCTOR and user.doctor.id!=doctor_id: raise HTTPException(403,"Không phải lịch của bạn")
    s=DoctorSchedule(doctor_id=doctor_id,**data.model_dump());db.add(s);db.commit();db.refresh(s);return s
@router.put("/doctors/{doctor_id}/schedules/{schedule_id}",response_model=ScheduleOut)
def update_schedule(doctor_id:int,schedule_id:int,data:ScheduleIn,db:Session=Depends(get_db),user=Depends(require_roles(Role.DOCTOR,Role.ADMIN))):
    s=db.get(DoctorSchedule,schedule_id)
    if not s or s.doctor_id!=doctor_id: raise HTTPException(404,"Không tìm thấy lịch làm việc")
    if user.role==Role.DOCTOR and user.doctor.id!=doctor_id: raise HTTPException(403,"Không phải lịch của bạn")
    for k,v in data.model_dump().items(): setattr(s,k,v)
    db.commit();db.refresh(s);return s
@router.get("/doctors/{doctor_id}/days-off",response_model=list[DayOffOut])
def days_off(doctor_id:int,db:Session=Depends(get_db)): return db.scalars(select(DoctorDayOff).where(DoctorDayOff.doctor_id==doctor_id).order_by(DoctorDayOff.date)).all()
@router.post("/doctors/{doctor_id}/days-off",response_model=DayOffOut)
def add_day_off(doctor_id:int,data:DayOffIn,db:Session=Depends(get_db),user=Depends(require_roles(Role.DOCTOR,Role.ADMIN))):
    if user.role==Role.DOCTOR and user.doctor.id!=doctor_id: raise HTTPException(403,"Không phải lịch của bạn")
    x=DoctorDayOff(doctor_id=doctor_id,**data.model_dump());db.add(x);db.commit();db.refresh(x);return x
@router.get("/doctors/me/appointments")
def doctor_appointments(db:Session=Depends(get_db),user=Depends(require_roles(Role.DOCTOR))):
    rows=db.scalars(select(Appointment).where(Appointment.doctor_id==user.doctor.id).order_by(Appointment.appointment_date.desc(),Appointment.start_time)).all()
    return [{"id":a.id,"patient_id":a.patient_id,"patient_name":a.patient.user.full_name,"phone":a.patient.user.phone,"date":a.appointment_date,"start_time":a.start_time,"reason":a.reason,"status":a.status,"visit_type":a.visit_type} for a in rows]
@router.patch("/appointments/{appointment_id}/start")
def start(appointment_id:int,db:Session=Depends(get_db),user=Depends(require_roles(Role.DOCTOR))):
    a=db.get(Appointment,appointment_id)
    if not a or a.doctor_id!=user.doctor.id: raise HTTPException(404,"Không tìm thấy lượt khám")
    if a.status!=AppointmentStatus.WAITING.value: raise HTTPException(400,"Chỉ WAITING mới bắt đầu khám")
    a.status=AppointmentStatus.IN_PROGRESS.value;a.started_at=datetime.utcnow();db.commit();return {"message":"Bắt đầu khám"}
@router.post("/appointments/{appointment_id}/medical-result")
def result(appointment_id:int,data:MedicalResultIn,db:Session=Depends(get_db),user=Depends(require_roles(Role.DOCTOR))):
    a=db.get(Appointment,appointment_id)
    if not a or a.doctor_id!=user.doctor.id: raise HTTPException(404,"Không tìm thấy lượt khám")
    if a.status!=AppointmentStatus.IN_PROGRESS.value: raise HTTPException(400,"Chỉ IN_PROGRESS mới nhập kết quả")
    r=a.medical_result or MedicalResult(appointment_id=a.id,diagnosis=data.diagnosis,notes=data.notes,prescription=data.prescription)
    if a.medical_result:
        r.diagnosis=data.diagnosis;r.notes=data.notes;r.prescription=data.prescription
    else: db.add(r)
    db.commit();return {"message":"Đã lưu kết quả khám"}
@router.patch("/appointments/{appointment_id}/complete")
def complete(appointment_id:int,db:Session=Depends(get_db),user=Depends(require_roles(Role.DOCTOR))):
    a=db.get(Appointment,appointment_id)
    if not a or a.doctor_id!=user.doctor.id: raise HTTPException(404,"Không tìm thấy lượt khám")
    if a.status!=AppointmentStatus.IN_PROGRESS.value: raise HTTPException(400,"Chỉ IN_PROGRESS mới hoàn thành")
    if not a.medical_result: raise HTTPException(400,"Cần nhập kết quả khám trước khi hoàn thành")
    a.status=AppointmentStatus.COMPLETED.value;a.completed_at=datetime.utcnow();db.commit();return {"message":"Đã hoàn thành khám"}
