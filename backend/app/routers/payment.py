from datetime import datetime, timezone
import base64, io
import qrcode
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import Payment, PaymentStatus, PaymentMethod, Role, User
from app.schemas.payment import PaymentOut
router=APIRouter(prefix="/api/payments",tags=["Payments"])
def qr_image(payload):
    img=qrcode.make(payload); buf=io.BytesIO(); img.save(buf,format="PNG"); return "data:image/png;base64,"+base64.b64encode(buf.getvalue()).decode()
def out(p):
    return PaymentOut(id=p.id,appointment_id=p.appointment_id,service_id=p.service_id,service_name=p.service.name,amount=p.amount,method=p.method,status=p.status,reference=p.reference,qr_payload=p.qr_payload,qr_image=qr_image(p.qr_payload) if p.method==PaymentMethod.QR.value and p.qr_payload else None,paid_at=p.paid_at.isoformat() if p.paid_at else None)
def owned(p,user): return user.role==Role.ADMIN or (user.role==Role.PATIENT and user.patient and p.appointment.patient_id==user.patient.id)
@router.get("/{appointment_id}",response_model=PaymentOut)
def get_payment(appointment_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    p=db.scalar(select(Payment).where(Payment.appointment_id==appointment_id))
    if not p or not owned(p,user): raise HTTPException(404,"Không tìm thấy thông tin thanh toán")
    return out(p)
@router.post("/{appointment_id}/confirm-demo",response_model=PaymentOut)
def confirm_demo(appointment_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    p=db.scalar(select(Payment).where(Payment.appointment_id==appointment_id))
    if not p or not owned(p,user): raise HTTPException(404,"Không tìm thấy thông tin thanh toán")
    if p.status!=PaymentStatus.PENDING.value: raise HTTPException(400,"Khoản thanh toán không ở trạng thái chờ thanh toán")
    p.status=PaymentStatus.PAID.value; p.paid_at=datetime.now(timezone.utc); db.commit(); db.refresh(p); return out(p)
@router.post("/{appointment_id}/pay-later",response_model=PaymentOut)
def pay_later(appointment_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    p=db.scalar(select(Payment).where(Payment.appointment_id==appointment_id))
    if not p or not owned(p,user): raise HTTPException(404,"Không tìm thấy thông tin thanh toán")
    if p.status not in {PaymentStatus.UNPAID.value,PaymentStatus.PENDING.value}: raise HTTPException(400,"Khoản thanh toán không thể chuyển sang thanh toán tại cơ sở")
    p.method=PaymentMethod.OFFLINE.value; p.status=PaymentStatus.UNPAID.value; p.qr_payload=None; db.commit(); db.refresh(p); return out(p)

@router.post("/{appointment_id}/refund",response_model=PaymentOut)
def refund(appointment_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    if user.role not in {Role.RECEPTIONIST,Role.ADMIN}: raise HTTPException(403,"Chỉ nhân viên tiếp nhận hoặc quản trị viên được xử lý hoàn tiền")
    p=db.scalar(select(Payment).where(Payment.appointment_id==appointment_id))
    if not p: raise HTTPException(404,"Không tìm thấy thông tin thanh toán")
    if p.status!=PaymentStatus.REFUND_PENDING.value: raise HTTPException(400,"Khoản thanh toán chưa ở trạng thái chờ hoàn tiền")
    p.status=PaymentStatus.REFUNDED.value; db.commit(); db.refresh(p); return out(p)
