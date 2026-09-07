from sqlalchemy import select
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import *

def seed_data():
    db=SessionLocal()
    try:
        if db.scalar(select(User).where(User.email=="admin@medschedule.local")): return
        specs=[Specialty(name="Tim mạch",description="Khám và theo dõi bệnh lý tim mạch."),Specialty(name="Nội tổng quát",description="Khám nội khoa tổng quát."),Specialty(name="Nhi khoa",description="Khám và theo dõi sức khỏe trẻ em.")]
        db.add_all(specs);db.flush()
        def add_user(name,email,role,phone):
            u=User(full_name=name,email=email,phone=phone,password_hash=hash_password("123456"),role=role);db.add(u);db.flush();return u
        admin=add_user("Quản trị viên","admin@medschedule.local",Role.ADMIN,"0900000001")
        rec=add_user("Lễ tân Demo","reception@medschedule.local",Role.RECEPTIONIST,"0900000002")
        doc1=add_user("Nguyễn Văn An","doctor@medschedule.local",Role.DOCTOR,"0900000003")
        doc2=add_user("Trần Minh Hà","doctor2@medschedule.local",Role.DOCTOR,"0900000004")
        pat=add_user("Nguyễn Hồng Huân","patient@medschedule.local",Role.PATIENT,"0900000005")
        p=Patient(user_id=pat.id);d1=Doctor(user_id=doc1.id,license_no="BS-001",bio="Bác sĩ chuyên Tim mạch, 10 năm kinh nghiệm.",room="P.201");d2=Doctor(user_id=doc2.id,license_no="BS-002",bio="Bác sĩ Nội tổng quát.",room="P.202");db.add_all([p,d1,d2]);db.flush()
        db.add_all([DoctorSpecialty(doctor_id=d1.id,specialty_id=specs[0].id),DoctorSpecialty(doctor_id=d2.id,specialty_id=specs[1].id)])
        for d in [d1,d2]:
            for wd in range(0,5): db.add(DoctorSchedule(doctor_id=d.id,weekday=wd,start_time="08:00",end_time="17:00",slot_minutes=30))
        db.commit()
    finally: db.close()
