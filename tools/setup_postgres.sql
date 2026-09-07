-- MedSchedule local PostgreSQL bootstrap
-- Run through tools/setup-local.bat. psql will ask for the postgres admin password.
SELECT 'CREATE ROLE meduser LOGIN PASSWORD ''medpass''' \
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'meduser')\gexec

SELECT 'CREATE DATABASE medical_appointments OWNER meduser' \
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'medical_appointments')\gexec

ALTER DATABASE medical_appointments OWNER TO meduser;
