# MedSchedule — Hệ thống quản lý lịch khám bệnh

Ứng dụng localhost bám theo quy trình trong tài liệu phân công 08/2026: bệnh nhân đặt lịch → `CONFIRMED` → lễ tân `CHECK-IN` → `WAITING` → bác sĩ `IN_PROGRESS` → `COMPLETED`; có `CANCELLED`, `NO_SHOW` và `WALK_IN` đúng định nghĩa nghiệp vụ.

## Tech stack

- Frontend: ReactJS + Vite 8 + Tailwind CSS + Axios
- Backend: Python + FastAPI + SQLAlchemy + Pydantic
- Database: PostgreSQL
- Migration: Alembic
- Authentication: JWT + Argon2 password hashing
- API docs: Swagger/OpenAPI tại `/docs`
- Source control: Git + GitHub ready
- Có Docker Compose tùy chọn, nhưng **không bắt buộc**.

## Chạy trên Windows không cần Docker (khuyến nghị cho máy không bật virtualization)

Cài trước:

1. Python 3.11+
2. Node.js LTS
3. PostgreSQL 14+ cho Windows

Sau khi giải nén ZIP, mở PowerShell/CMD tại thư mục `medical-appointment-system` và chạy:

```bat
run-local.bat
```

Script sẽ:

- tạo `backend\.venv`;
- cài Python dependencies;
- tạo `backend\.env` nếu chưa có;
- tìm `psql.exe` trong PATH hoặc thư mục PostgreSQL mặc định;
- tạo role `meduser` với mật khẩu `medpass` và database `medical_appointments`;
- chạy `alembic upgrade head`;
- seed tài khoản demo;
- mở FastAPI và React/Vite ở 2 cửa sổ riêng.

Lệnh tương đương thủ công:

```bat
setup-local.bat
```

Sau đó backend:

```bat
cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```bat
cd frontend
npm install
npm run dev -- --host 127.0.0.1
```

Mở:

- Frontend: http://localhost:5173
- Swagger: http://localhost:8000/docs
- Health: http://localhost:8000/api/health

### Nếu PostgreSQL dùng user/password khác

Chỉnh `backend\.env`:

```env
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/medical_appointments
JWT_SECRET=change-this-secret-in-production
CORS_ORIGINS=http://localhost:5173
```

Sau đó chạy lại:

```bat
cd backend
.venv\Scripts\alembic.exe upgrade head
```

Nếu không muốn dùng script tự tạo database, có thể tạo database `medical_appointments` thủ công rồi giữ nguyên `DATABASE_URL` phù hợp.

## Tài khoản demo

Mật khẩu tất cả tài khoản demo: `123456`

| Role | Email |
|---|---|
| ADMIN | admin@medschedule.local |
| RECEPTIONIST | reception@medschedule.local |
| DOCTOR | doctor@medschedule.local |
| DOCTOR | doctor2@medschedule.local |
| PATIENT | patient@medschedule.local |

## Luồng kiểm thử E2E

### PATIENT

Đăng ký/đăng nhập → chuyên khoa → bác sĩ → ngày → slot → lý do → đặt lịch `CONFIRMED` → xem chi tiết → đổi lịch → hủy lịch `CANCELLED`.

Kiểm tra lỗi: double booking slot, bệnh nhân tự trùng giờ, slot đã qua, ngày bác sĩ nghỉ, đổi sang slot đã có người đặt.

### RECEPTIONIST

Xem lịch hôm nay → tìm bệnh nhân/mã lịch/SĐT → check-in `CHECKED_IN` → vào `WAITING` → gọi queue → tạo `WALK_IN` → đánh dấu `NO_SHOW` sau hơn 15 phút.

Ưu tiên queue: appointment check-in đúng giờ → bệnh nhân trễ được nhận → walk-in.

### DOCTOR

Xem `WAITING` → gọi/bắt đầu `IN_PROGRESS` → nhập chẩn đoán/kết quả → `COMPLETED`. Bác sĩ chỉ được thao tác appointment của chính mình.

### ADMIN

Dashboard: tổng lịch hôm nay, waiting, in-progress, completed, cancelled, no-show.

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

## Quy tắc nghiệp vụ

- Không đặt lịch vào ngày bác sĩ không làm việc/ngày nghỉ.
- Không chọn slot đã qua trong ngày hiện tại.
- Không double-booking slot của bác sĩ.
- Một bệnh nhân không được đặt hai lịch cùng giờ.
- Hủy chỉ áp dụng cho `CONFIRMED`.
- Đổi lịch phải kiểm tra slot mới trước rồi mới giải phóng slot cũ.
- `CONFIRMED → CHECKED_IN → WAITING`.
- `NO_SHOW` chỉ sau hơn 15 phút kể từ giờ hẹn.
- `WAITING → IN_PROGRESS → COMPLETED`.
- Bác sĩ chỉ được thao tác appointment của chính mình.
- API luôn kiểm tra JWT/role; ẩn nút trên frontend không thay thế authorization.
- `WALK_IN` là loại lượt khám, không phải trạng thái appointment.

## Docker (tùy chọn)

Nếu máy có Docker Desktop và virtualization hoạt động:

```bash
docker compose up --build
```

Nếu Docker Desktop báo `Virtualization support not detected`, bỏ qua Docker và dùng `run-local.bat` ở trên.

## Test / chất lượng

`docs/TEST_REPORT.md` ghi lại phạm vi kiểm thử. Trong môi trường build artifact không có Docker/PostgreSQL runtime nên không tuyên bố giả rằng browser E2E/DB integration đã chạy thành công ở đây. Source đã được kiểm tra compile/static structure; khi chạy local hãy thực hiện checklist E2E bên trên.


## Production deployment

- Backend: Render, Root Directory `backend`, Python 3.13.x, `pip install -r requirements.txt`, `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- Frontend: Vercel, Root Directory `frontend`, Framework Vite, build `npm run build`, output `dist`.
- Frontend environment: `VITE_API_BASE_URL=https://<your-render-service>/api`.
- Backend environment: `DATABASE_URL`, `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES`, `CORS_ORIGINS`.
- Do not commit `.env` or production secrets.

## Thanh toán
Bệnh nhân xem giá niêm yết mẫu theo chuyên khoa và có thể chọn thanh toán tại cơ sở hoặc QR mô phỏng. QR chỉ phục vụ demo đồ án, không kết nối ngân hàng thật. Lịch đã thanh toán mà bị hủy/NO_SHOW sẽ chuyển `REFUND_PENDING` để nhân viên xử lý.


## Admin account management (v14)
- Admin has a dedicated **Tài khoản** tab to search users across PATIENT / RECEPTIONIST / DOCTOR / ADMIN.
- Admin can edit account name, email, phone and active/locked status.
- Admin can reset passwords for any account; doctor and patient edit dialogs also expose **Đặt lại mật khẩu**.
- Doctor edit now allows updating the login email while enforcing uniqueness.
