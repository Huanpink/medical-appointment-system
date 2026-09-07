from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User, Patient
from app.schemas.auth import RegisterIn, LoginIn, PasswordChange, TokenOut, UserOut

router=APIRouter(prefix="/api/auth", tags=["Authentication"])
@router.post("/register", response_model=TokenOut)
def register(data:RegisterIn, db:Session=Depends(get_db)):
    if db.scalar(select(User).where(User.email==data.email.lower())):
        raise HTTPException(409,"Email đã tồn tại")
    user=User(full_name=data.full_name.strip(),email=data.email.lower(),phone=data.phone,password_hash=hash_password(data.password))
    db.add(user); db.flush(); db.add(Patient(user_id=user.id)); db.commit(); db.refresh(user)
    return {"access_token":create_access_token(str(user.id),user.role.value),"user":user}
@router.post("/login", response_model=TokenOut)
def login(data:LoginIn, db:Session=Depends(get_db)):
    user=db.scalar(select(User).where(User.email==data.email.lower()))
    if not user or not verify_password(data.password,user.password_hash): raise HTTPException(401,"Email hoặc mật khẩu không đúng")
    return {"access_token":create_access_token(str(user.id),user.role.value),"user":user}
@router.get("/me",response_model=UserOut)
def me(user:User=Depends(get_current_user)): return user

@router.patch("/password")
def change_password(data: PasswordChange, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(400, "Mật khẩu hiện tại không đúng")
    user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"message": "Đổi mật khẩu thành công"}
