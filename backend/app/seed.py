from sqlalchemy import select
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import *

def seed_data():
    db=SessionLocal()
    try:
        existing_specs={x.name:x for x in db.scalars(select(Specialty)).all()}
        needed=[("Tim mạch","Khám và theo dõi bệnh lý tim mạch."),("Nội tổng quát","Khám nội khoa tổng quát."),("Nhi khoa","Khám và theo dõi sức khỏe trẻ em.")]
        specs=[]
        for name,desc in needed:
            obj=existing_specs.get(name)
            if not obj:
                obj=Specialty(name=name,description=desc); db.add(obj); db.flush()
            specs.append(obj)

        def ensure_services():
            desired=[
                ("KHAM-TM", specs[0].id, "Khám chuyên khoa Tim mạch", "Khám và tư vấn bệnh lý tim mạch.", 350000),
                ("KHAM-NOITQ", specs[1].id, "Khám Nội tổng quát", "Khám và tư vấn nội khoa tổng quát.", 250000),
                ("KHAM-NHI", specs[2].id, "Khám Nhi khoa", "Khám và tư vấn sức khỏe trẻ em.", 300000),
            ]
            for code,sid,name,desc,price in desired:
                obj=db.scalar(select(Service).where(Service.code==code))
                if not obj:
                    db.add(Service(specialty_id=sid,code=code,name=name,description=desc,price=price,active=True))

        if db.scalar(select(User).where(User.email=="admin@medschedule.local")):
            ensure_services(); db.commit(); return

        def add_user(name,email,role,phone):
            u=User(full_name=name,email=email,phone=phone,password_hash=hash_password("123456"),role=role); db.add(u); db.flush(); return u
        add_user("Quản trị viên","admin@medschedule.local",Role.ADMIN,"0900000001")
        add_user("Lễ tân Demo","reception@medschedule.local",Role.RECEPTIONIST,"0900000002")
        doc1=add_user("Nguyễn Văn An","doctor@medschedule.local",Role.DOCTOR,"0900000003")
        doc2=add_user("Trần Minh Hà","doctor2@medschedule.local",Role.DOCTOR,"0900000004")
        pat=add_user("Nguyễn Hồng Huân","patient@medschedule.local",Role.PATIENT,"0900000005")
        p=Patient(user_id=pat.id)
        d1=Doctor(user_id=doc1.id,license_no="BS-001",bio="Bác sĩ chuyên Tim mạch, 10 năm kinh nghiệm.",room="P.201")
        d2=Doctor(user_id=doc2.id,license_no="BS-002",bio="Bác sĩ Nội tổng quát.",room="P.202")
        db.add_all([p,d1,d2]); db.flush()
        db.add_all([DoctorSpecialty(doctor_id=d1.id,specialty_id=specs[0].id),DoctorSpecialty(doctor_id=d2.id,specialty_id=specs[1].id)])
        ensure_services()
        for d in [d1,d2]:
            for wd in range(0,5): db.add(DoctorSchedule(doctor_id=d.id,weekday=wd,start_time="08:00",end_time="17:00",slot_minutes=30))
        db.commit()
    finally:
        db.close()
