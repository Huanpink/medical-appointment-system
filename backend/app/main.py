from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import Base, engine
from app.routers import auth, master, booking, reception, doctor, admin
from app.seed import seed_data

app=FastAPI(title="MedSchedule API",version="1.0.0",description="Hệ thống quản lý lịch khám bệnh")
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in __import__('app.core.config',fromlist=['settings']).settings.cors_origins.split(',')],allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
app.include_router(auth.router);app.include_router(master.router);app.include_router(booking.router);app.include_router(reception.router);app.include_router(doctor.router);app.include_router(admin.router)
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    seed_data()
@app.get("/")
def root(): return {"service":"MedSchedule API","docs":"/docs"}

@app.get("/healthz")
def healthz(): return {"status":"ok"}

@app.get("/api/health")
def health(): return {"status":"ok","service":"medschedule-api"}
