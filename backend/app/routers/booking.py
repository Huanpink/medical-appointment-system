from datetime import datetime, date as date_cls, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import *
from app.schemas.appointment import AppointmentCreate, AppointmentOut, RescheduleIn

router=APIRouter(prefix="/api",tags=["Booking"])
def slot_available(db,doctor_id,d,tm,exclude_id=None):
    ap=db.scalar(select(Appointment).where(Appointment.doctor_id==doctor_id,Appointment.appointment_date==d,Appointment.start_time==tm,Appointment.status.notin_([AppointmentStatus.CANCELLED.value,AppointmentStatus.NO_SHOW.value]), *( [Appointment.id!=exclude_id] if exclude_id else [] )))
    return ap is None
def get_schedule(db,doctor_id,d):
    wd=date_cls.fromisoformat(d).weekday()
    if db.scalar(select(DoctorDayOff).where(DoctorDayOff.doctor_id==doctor_id,DoctorDayOff.date==d)): return None
    return db.scalar(select(DoctorSchedule).where(DoctorSchedule.doctor_id==doctor_id,DoctorSchedule.weekday==wd))
def build_slots(schedule, d, now=None):
    start=datetime.combine(date_cls.fromisoformat(d),datetime.strptime(schedule.start_time,"%H:%M").time())
    end=datetime.combine(date_cls.fromisoformat(d),datetime.strptime(schedule.end_time,"%H:%M").time())
    out=[]; cur=start
    while cur+timedelta(minutes=schedule.slot_minutes)<=end:
        if not now or cur>now: out.append((cur.strftime("%H:%M"),(cur+timedelta(minutes=schedule.slot_minutes)).strftime("%H:%M")))
        cur+=timedelta(minutes=schedule.slot_minutes)
    return out
@router.get("/doctors/{doctor_id}/available-slots")
def available_slots(doctor_id:int,date:str=Query(alias="date"),db:Session=Depends(get_db)):
    try: date_cls.fromisoformat(date)
    except: raise HTTPException(400,"Ngày không hợp lệ")
    s=get_schedule(db,doctor_id,date)
    if not s: return []
    now=datetime.now() if date==datetime.now().strftime("%Y-%m-%d") else None
    booked={a.start_time for a in db.scalars(select(Appointment).where(Appointment.doctor_id==doctor_id,Appointment.appointment_date==date,Appointment.status.notin_([AppointmentStatus.CANCELLED.value,AppointmentStatus.NO_SHOW.value])))}
    return [{"start_time":st,"end_time":et,"available":st not in booked} for st,et in build_slots(s,date,now) if st not in booked]

def appointment_payload(a:Appointment):
    specialty=a.doctor.specialties[0].specialty.name if a.doctor.specialties else None
    return AppointmentOut(id=a.id,patient_id=a.patient_id,doctor_id=a.doctor_id,doctor_name=a.doctor.user.full_name,appointment_date=a.appointment_date,start_time=a.start_time,end_time=a.end_time,reason=a.reason,status=a.status,visit_type=a.visit_type,specialty_name=specialty,patient_name=a.patient.user.full_name)
@router.post("/appointments",response_model=AppointmentOut)
def create_appointment(data:AppointmentCreate,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    if user.role!=Role.PATIENT: raise HTTPException(403,"Chỉ bệnh nhân được đặt lịch")
    p=user.patient; s=get_schedule(db,data.doctor_id,data.appointment_date)
    if not s: raise HTTPException(400,"Bác sĩ không làm việc ngày này")
    slots=dict(build_slots(s,data.appointment_date,datetime.now() if data.appointment_date==datetime.now().strftime("%Y-%m-%d") else None))
    if data.start_time not in slots: raise HTTPException(400,"Slot không hợp lệ hoặc đã qua")
    if not slot_available(db,data.doctor_id,data.appointment_date,data.start_time): raise HTTPException(409,"Slot đã được đặt")
    end=slots[data.start_time]
    same=db.scalar(select(Appointment).where(Appointment.patient_id==p.id,Appointment.appointment_date==data.appointment_date,Appointment.start_time==data.start_time,Appointment.status.notin_([AppointmentStatus.CANCELLED.value,AppointmentStatus.NO_SHOW.value])))
    if same: raise HTTPException(409,"Bạn đã có lịch trùng giờ")
    a=Appointment(patient_id=p.id,doctor_id=data.doctor_id,appointment_date=data.appointment_date,start_time=data.start_time,end_time=end,reason=data.reason,status=AppointmentStatus.CONFIRMED.value,visit_type=VisitType.APPOINTMENT.value)
    db.add(a); db.commit(); db.refresh(a); return appointment_payload(a)
@router.get("/patients/me/appointments",response_model=list[AppointmentOut])
def my_appointments(db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    return [appointment_payload(a) for a in db.scalars(select(Appointment).where(Appointment.patient_id==user.patient.id).order_by(Appointment.appointment_date.desc(),Appointment.start_time.desc())).all()]
@router.get("/appointments/{appointment_id}",response_model=AppointmentOut)
def get_appointment(appointment_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    a=db.get(Appointment,appointment_id)
    if not a: raise HTTPException(404,"Không tìm thấy lịch")
    if user.role==Role.PATIENT and a.patient_id!=user.patient.id: raise HTTPException(403,"Không có quyền")
    return appointment_payload(a)
@router.patch("/appointments/{appointment_id}/cancel")
def cancel(appointment_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    a=db.get(Appointment,appointment_id)
    if not a or (user.role==Role.PATIENT and a.patient_id!=user.patient.id): raise HTTPException(404,"Không tìm thấy lịch")
    if a.status!=AppointmentStatus.CONFIRMED.value: raise HTTPException(400,"Chỉ lịch CONFIRMED mới được hủy")
    a.status=AppointmentStatus.CANCELLED.value; db.commit(); return {"message":"Đã hủy lịch"}
@router.patch("/appointments/{appointment_id}/reschedule",response_model=AppointmentOut)
def reschedule(appointment_id:int,data:RescheduleIn,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    a=db.get(Appointment,appointment_id)
    if not a or (user.role==Role.PATIENT and a.patient_id!=user.patient.id): raise HTTPException(404,"Không tìm thấy lịch")
    if a.status!=AppointmentStatus.CONFIRMED.value: raise HTTPException(400,"Chỉ lịch CONFIRMED mới được đổi")
    s=get_schedule(db,a.doctor_id,data.appointment_date)
    if not s: raise HTTPException(400,"Bác sĩ không làm việc ngày này")
    slots=dict(build_slots(s,data.appointment_date,datetime.now() if data.appointment_date==datetime.now().strftime("%Y-%m-%d") else None))
    if data.start_time not in slots or not slot_available(db,a.doctor_id,data.appointment_date,data.start_time,a.id): raise HTTPException(409,"Khung giờ mới không còn trống")
    a.appointment_date=data.appointment_date;a.start_time=data.start_time;a.end_time=slots[data.start_time];db.commit();db.refresh(a);return appointment_payload(a)
