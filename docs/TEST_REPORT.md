# Test Report — MedSchedule

## Static checks completed

- Python application compile check: passed (`python -m compileall -q backend/app`).
- Project structure reviewed: frontend/backend/Alembic/routers/services/models/schemas.
- Axios service layer present; frontend does not hard-code API URLs in page components.
- Alembic now reads `DATABASE_URL` from `backend/.env` instead of relying only on a hard-coded connection string.
- Local Windows start path added so Docker is optional.

## Manual E2E checklist to run on a Windows machine

1. Register → login → book → `CONFIRMED`.
2. Duplicate same doctor/slot → rejected.
3. Duplicate patient/time → rejected.
4. Cancel → `CANCELLED`, slot available again.
5. Reschedule → new slot accepted, old slot released.
6. Reception check-in → `CHECKED_IN` → `WAITING`.
7. Late/no-show rule (>15 minutes) enforced.
8. Walk-in enters queue as `WALK_IN` type.
9. Queue priority checked.
10. Doctor starts `WAITING` → `IN_PROGRESS`.
11. Medical result saved and appointment completed → `COMPLETED`.
12. Doctor cannot modify another doctor's appointment.
13. Role-protected API returns authorization error for invalid role.
14. Admin dashboard counters load.
15. Swagger endpoints respond at `/docs`.

## Environment limitation

The build environment used to prepare this ZIP did not provide a running Docker daemon or PostgreSQL server and did not have unrestricted package-registry access. Therefore no claim is made that full browser E2E and live PostgreSQL integration were executed in that build environment. The project includes Windows-local bootstrap scripts to run those checks on the target machine.
