# MedSchedule — Hệ thống quản lý lịch khám bệnh

Ứng dụng localhost theo đúng luồng nghiệp vụ trong tài liệu phân công tháng 08/2026: bệnh nhân đặt lịch → CONFIRMED → lễ tân CHECK-IN → WAITING → bác sĩ IN_PROGRESS → COMPLETED; có CANCELLED, NO_SHOW và WALK_IN theo đúng định nghĩa nghiệp vụ.

## Tech stack

- Frontend: ReactJS + Vite 8 + Tailwind CSS + Axios
- Backend: Python + FastAPI + SQLAlchemy + Pydantic
- Database: PostgreSQL
- Migration: Alembic
- Authentication: JWT + password hashing Argon2
- API docs: Swagger/OpenAPI tại `/docs`
- Source control: Git/GitHub ready
- Local infrastructure: Docker Compose

## Cấu trúc

```text
medical-appointment-system/
├─ frontend/
├─ backend/
├─ docs/
├─ docker-compose.yml
├─ .env.example
├─ .gitignore
└─ README.md
```

## Chạy nhanh bằng Docker

Yêu cầu Docker Desktop.

```bash
docker compose up --build
```

Sau đó mở:

- Frontend: http://localhost:5173
- Swagger: http://localhost:8000/docs
- Health: http://localhost:8000/api/health
- PostgreSQL: localhost:5432

Backend tự chạy `alembic upgrade head`, sau đó seed dữ liệu demo.

## Chạy không dùng Docker

Cần PostgreSQL chạy local và tạo database `medical_appointments`.

Backend:

```bash
cd backend
python -m venv .venv
# Windows
.venv\\Scripts\\activate
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Mặc định frontend gọi `http://localhost:8000/api`. Có thể đổi bằng `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

## Tài khoản demo

Mật khẩu tất cả tài khoản demo: `123456`

| Role | Email |
|---|---|
| ADMIN | admin@medschedule.local |
| RECEPTIONIST | reception@medschedule.local |
| DOCTOR | doctor@medschedule.local |
| DOCTOR | doctor2@medschedule.local |
| PATIENT | patient@medschedule.local |

## Luồng kiểm thử E2E đề xuất

### Patient
1. Register/Login.
2. Chọn chuyên khoa.
3. Chọn bác sĩ.
4. Chọn ngày làm việc.
5. Chọn slot trống.
6. Nhập lý do và đặt lịch → `CONFIRMED`.
7. Xem chi tiết lịch.
8. Đổi lịch sang slot khác.
9. Hủy lịch → `CANCELLED` và slot được giải phóng.
10. Kiểm tra không đặt được cùng slot hoặc cùng giờ.

### Receptionist
1. Đăng nhập.
2. Xem lịch hôm nay.
3. Check-in → `CHECKED_IN` → `WAITING`.
4. Gọi bệnh nhân trong queue.
5. Tạo `WALK_IN`.
6. Đánh dấu `NO_SHOW` chỉ sau quá 15 phút.
7. Kiểm tra ưu tiên queue: appointment đúng giờ → bệnh nhân trễ → walk-in.

### Doctor
1. Đăng nhập.
2. Xem bệnh nhân WAITING.
3. Bắt đầu khám → `IN_PROGRESS`.
4. Nhập chẩn đoán / ghi chú / đơn thuốc.
5. Hoàn thành → `COMPLETED`.
6. Kiểm tra bác sĩ không thể thao tác appointment của bác sĩ khác.

### Admin
1. Đăng nhập.
2. Xem dashboard hôm nay: tổng lịch, waiting, in-progress, completed, cancelled, no-show.

## API chính

### Auth
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `PATCH /api/auth/password`

### Master data
- `GET /api/specialties`
- `GET /api/doctors`
- `GET /api/doctors/{id}`
- `GET /api/patients/{id}`
- `PUT /api/patients/{id}`
- `GET /api/patients/search?q=...`

### Booking
- `GET /api/doctors/{id}/available-slots?date=...`
- `POST /api/appointments`
- `GET /api/patients/me/appointments`
- `GET /api/appointments/{id}`
- `PATCH /api/appointments/{id}/cancel`
- `PATCH /api/appointments/{id}/reschedule`

### Reception / Queue
- `GET /api/appointments?date=...`
- `PATCH /api/appointments/{id}/check-in`
- `PATCH /api/appointments/{id}/no-show`
- `POST /api/walk-ins`
- `GET /api/queue?doctorId=...`
- `POST /api/queue`
- `PATCH /api/queue/{id}/call`

### Doctor / Schedule / Examination
- `GET /api/doctors/{id}/schedules`
- `POST /api/doctors/{id}/schedules`
- `PUT /api/doctors/{id}/schedules/{scheduleId}`
- `GET /api/doctors/{id}/days-off`
- `POST /api/doctors/{id}/days-off`
- `GET /api/doctors/me/appointments`
- `PATCH /api/appointments/{id}/start`
- `POST /api/appointments/{id}/medical-result`
- `PATCH /api/appointments/{id}/complete`

## Quy tắc nghiệp vụ được khóa trong backend

- Không đặt lịch vào ngày bác sĩ không làm việc hoặc ngày nghỉ.
- Không chọn slot đã qua trong ngày hiện tại.
- Không double-booking một slot của bác sĩ.
- Một bệnh nhân không được đặt hai lịch cùng giờ.
- Hủy chỉ áp dụng cho `CONFIRMED`.
- Đổi lịch chỉ áp dụng cho `CONFIRMED` và kiểm tra slot mới trước.
- `CONFIRMED → CHECKED_IN → WAITING`.
- `NO_SHOW` chỉ sau hơn 15 phút kể từ giờ hẹn.
- `WAITING → IN_PROGRESS → COMPLETED`.
- Bác sĩ chỉ được thao tác appointment thuộc chính mình.
- API kiểm tra JWT và role; ẩn nút trên frontend không được dùng thay cho authorization.

## Test / kiểm tra chất lượng

Trong gói có `docs/TEST_REPORT.md`. Môi trường tạo artifact này không có Docker/PostgreSQL và không có kết nối package registry, vì vậy không thể trung thực tuyên bố đã chạy browser E2E/DB integration trên chính máy build. Đã thực hiện static validation, Python compile check và kiểm tra cấu trúc route/service/config; báo cáo nêu rõ phần nào cần chạy khi giải nén trên máy có Docker.

## Git

Khuyến nghị:

```bash
git init
git add .
git commit -m "feat: complete medical appointment system"
git branch -M main
git remote add origin <your-github-repository>
git push -u origin main
```
