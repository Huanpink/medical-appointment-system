from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.core.database import Base, engine
from app.routers import auth, master, booking, reception, doctor, admin, payment
from app.seed import seed_data

app=FastAPI(title="MedSchedule API",version="1.0.0",description="Hệ thống quản lý lịch khám bệnh")
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in __import__('app.core.config',fromlist=['settings']).settings.cors_origins.split(',')],allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
app.include_router(auth.router);app.include_router(master.router);app.include_router(booking.router);app.include_router(reception.router);app.include_router(doctor.router);app.include_router(admin.router);app.include_router(payment.router)
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    # The booking rule requires a cancelled/no-show slot to become reusable.
    # Replace the old full unique constraint with an active-slot partial index.
    with engine.begin() as conn:
        if engine.dialect.name in {"postgresql", "sqlite"}:
            if engine.dialect.name == "postgresql":
                conn.execute(text("ALTER TABLE appointments DROP CONSTRAINT IF EXISTS uq_doctor_slot"))
                conn.execute(text("ALTER TABLE appointments ADD COLUMN IF NOT EXISTS service_id INTEGER"))
                conn.execute(text("ALTER TABLE appointments DROP CONSTRAINT IF EXISTS appointments_service_id_fkey"))
                conn.execute(text("ALTER TABLE appointments ADD CONSTRAINT appointments_service_id_fkey FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE RESTRICT"))
            else:
                conn.execute(text("DROP INDEX IF EXISTS uq_doctor_slot"))
                try: conn.execute(text("ALTER TABLE appointments ADD COLUMN service_id INTEGER"))
                except Exception: pass
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_doctor_slot_active ON appointments (doctor_id, appointment_date, start_time) WHERE status NOT IN ('CANCELLED', 'NO_SHOW')"))
    seed_data()
@app.get("/")
def root(): return {"service":"MedSchedule API","docs":"/docs"}

@app.get("/healthz")
def healthz(): return {"status":"ok"}

@app.get("/api/health")
def health(): return {"status":"ok","service":"medschedule-api"}
