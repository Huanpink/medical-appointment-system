from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import require_roles
from app.models import Appointment, AppointmentStatus, Role
router=APIRouter(prefix="/api/admin",tags=["Admin"])
@router.get("/dashboard")
def dashboard(db:Session=Depends(get_db),user=Depends(require_roles(Role.ADMIN))):
    d=datetime.now().strftime('%Y-%m-%d')
    counts={s.value:db.scalar(select(func.count()).select_from(Appointment).where(Appointment.appointment_date==d,Appointment.status==s.value)) or 0 for s in AppointmentStatus}
    return {"date":d,"total_today":sum(counts.values()),"waiting":counts[AppointmentStatus.WAITING.value],"completed":counts[AppointmentStatus.COMPLETED.value],"cancelled":counts[AppointmentStatus.CANCELLED.value],"no_show":counts[AppointmentStatus.NO_SHOW.value],"in_progress":counts[AppointmentStatus.IN_PROGRESS.value]}
