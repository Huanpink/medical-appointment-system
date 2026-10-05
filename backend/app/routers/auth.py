from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User, Patient
from app.schemas.auth import RegisterIn, PasswordChange, TokenOut, UserOut

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def _json_body(request: Request) -> dict[str, Any]:
    # FastAPI will normally return 422 before entering the handler for an invalid
    # Pydantic body. Parsing the request manually lets us return a stable, simple
    # JSON error for the demo/frontend instead of a validation object that React
    # could accidentally try to render.
    return {}


@router.post("/register", response_model=TokenOut)
async def register(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Dữ liệu đăng ký không hợp lệ")

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Dữ liệu đăng ký không hợp lệ")
    try:
        data = RegisterIn.model_validate(payload)
    except Exception:
        raise HTTPException(status_code=422, detail="Thông tin đăng ký chưa đầy đủ hoặc không hợp lệ")

    email = data.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "Email đã tồn tại")
    user = User(
        full_name=data.full_name.strip(),
        email=email,
        phone=data.phone,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    db.flush()
    db.add(Patient(user_id=user.id))
    db.commit()
    db.refresh(user)
    return {"access_token": create_access_token(str(user.id), user.role.value), "user": user}


@router.post("/login", response_model=TokenOut)
async def login(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Dữ liệu đăng nhập không hợp lệ")

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Dữ liệu đăng nhập không hợp lệ")

    email = str(payload.get("email", "")).strip().lower()
    password = payload.get("password", "")
    if not email or not isinstance(password, str) or not password:
        raise HTTPException(status_code=400, detail="Vui lòng nhập email và mật khẩu")

    user = db.scalar(select(User).where(User.email == email))
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(401, "Email hoặc mật khẩu không đúng")
    return {"access_token": create_access_token(str(user.id), user.role.value), "user": user}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.patch("/password")
def change_password(
    data: PasswordChange,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(400, "Mật khẩu hiện tại không đúng")
    user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"message": "Đổi mật khẩu thành công"}
