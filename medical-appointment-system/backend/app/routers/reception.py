from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import require_roles
from app.models import *
from app.schemas.appointment import WalkInIn, QueueOut

router=APIRouter(prefix="/api",tags=["Reception & Queue"])
def queue_payload(q):
    a=q.appointment
    return QueueOut(id=q.id,appointment_id=a.id,queue_no=q.queue_no,patient_name=a.patient.user.full_name,doctor_name=a.doctor.user.full_name,appointment_date=a.appointment_date,start_time=a.start_time,priority=q.priority,status=a.status,called_at=q.called_at.isoformat() if q.called_at else None)
def next_queue_no(db,doctor_id):
    n=db.scalar(select(func.max(QueueEntry.queue_no)).join(Appointment).where(Appointment.doctor_id==doctor_id,Appointment.appointment_date==datetime.now().strftime('%Y-%m-%d'))) or 0
    return n+1
@router.get("/appointments")
def appointments(date:str|None=None,db:Session=Depends(get_db),user=Depends(require_roles(Role.RECEPTIONIST,Role.ADMIN))):
    d=date or datetime.now().strftime('%Y-%m-%d')
    rows=db.scalars(select(Appointment).where(Appointment.appointment_date==d).order_by(Appointment.start_time)).all()
    return [{"id":a.id,"patient_id":a.patient_id,"patient_name":a.patient.user.full_name,"phone":a.patient.user.phone,"doctor_id":a.doctor_id,"doctor_name":a.doctor.user.full_name,"date":a.appointment_date,"start_time":a.start_time,"status":a.status,"visit_type":a.visit_type} for a in rows]
@router.patch("/appointments/{appointment_id}/check-in")
def check_in(appointment_id:int,db:Session=Depends(get_db),user=Depends(require_roles(Role.RECEPTIONIST,Role.ADMIN))):
    a=db.get(Appointment,appointment_id)
    if not a: raise HTTPException(404,"Không tìm thấy lịch")
    if a.status!=AppointmentStatus.CONFIRMED.value: raise HTTPException(400,"Chỉ CONFIRMED mới check-in")
    a.status=AppointmentStatus.CHECKED_IN.value;a.checked_in_at=datetime.now(timezone.utc)
    q=QueueEntry(appointment_id=a.id,queue_no=next_queue_no(db,a.doctor_id),priority=1 if a.start_time>=datetime.now().strftime('%H:%M') else 2)
    db.add(q);a.status=AppointmentStatus.WAITING.value;db.commit();return {"message":"Check-in thành công","status":a.status,"queue_no":q.queue_no}
@router.patch("/appointments/{appointment_id}/no-show")
def no_show(appointment_id:int,db:Session=Depends(get_db),user=Depends(require_roles(Role.RECEPTIONIST,Role.ADMIN))):
    a=db.get(Appointment,appointment_id)
    if not a: raise HTTPException(404,"Không tìm thấy lịch")
    if a.status not in [AppointmentStatus.CONFIRMED.value]: raise HTTPException(400,"Lịch không ở trạng thái phù hợp")
    now = datetime.now()
    scheduled = datetime.strptime(f"{a.appointment_date} {a.start_time}", "%Y-%m-%d %H:%M")
    if now < scheduled + __import__('datetime').timedelta(minutes=15):
        raise HTTPException(400,"Chỉ được đánh dấu NO_SHOW sau 15 phút kể từ giờ hẹn")
    a.status=AppointmentStatus.NO_SHOW.value;db.commit();return {"message":"Đã đánh dấu NO_SHOW"}
@router.post("/walk-ins",response_model=QueueOut)
def walk_in(data:WalkInIn,db:Session=Depends(get_db),user=Depends(require_roles(Role.RECEPTIONIST,Role.ADMIN))):
    p=db.get(Patient,data.patient_id);d=db.get(Doctor,data.doctor_id)
    if not p or not d: raise HTTPException(404,"Không tìm thấy bệnh nhân/bác sĩ")
    now=datetime.now().strftime('%H:%M')
    a=Appointment(patient_id=p.id,doctor_id=d.id,appointment_date=datetime.now().strftime('%Y-%m-%d'),start_time=now,end_time=now,reason=data.reason,status=AppointmentStatus.WAITING.value,visit_type=VisitType.WALK_IN.value)
    db.add(a);db.flush();q=QueueEntry(appointment_id=a.id,queue_no=next_queue_no(db,d.id),priority=3);db.add(q);db.commit();db.refresh(q);return queue_payload(q)
@router.get("/queue",response_model=list[QueueOut])
def queue(doctorId:int|None=Query(default=None),db:Session=Depends(get_db),user=Depends(require_roles(Role.RECEPTIONIST,Role.ADMIN,Role.DOCTOR))):
    stmt=select(QueueEntry).join(Appointment).where(Appointment.status==AppointmentStatus.WAITING.value,Appointment.appointment_date==datetime.now().strftime('%Y-%m-%d')).order_by(QueueEntry.priority,QueueEntry.queue_no)
    if doctorId: stmt=stmt.where(Appointment.doctor_id==doctorId)
    return [queue_payload(q) for q in db.scalars(stmt).all()]
@router.post("/queue")
def add_to_queue(payload:dict=Body(...),db:Session=Depends(get_db),user=Depends(require_roles(Role.RECEPTIONIST,Role.ADMIN))):
    appointment_id = int(payload.get("appointment_id", 0))
    a=db.get(Appointment,appointment_id)
    if not a: raise HTTPException(404,"Không tìm thấy lịch")
    if a.status!=AppointmentStatus.CHECKED_IN.value: raise HTTPException(400,"Appointment phải CHECKED_IN")
    a.status=AppointmentStatus.WAITING.value;q=QueueEntry(appointment_id=a.id,queue_no=next_queue_no(db,a.doctor_id),priority=1);db.add(q);db.commit();return {"message":"Đã vào hàng chờ"}
@router.patch("/queue/{queue_id}/call")
def call_queue(queue_id:int,db:Session=Depends(get_db),user=Depends(require_roles(Role.RECEPTIONIST,Role.ADMIN,Role.DOCTOR))):
    q=db.get(QueueEntry,queue_id)
    if not q or q.appointment.status!=AppointmentStatus.WAITING.value: raise HTTPException(404,"Không có lượt chờ")
    q.called_at=datetime.now(timezone.utc);db.commit();return {"message":"Đã gọi bệnh nhân","queue":queue_payload(q)}
