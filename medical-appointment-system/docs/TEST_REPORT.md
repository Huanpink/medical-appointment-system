# Test / Deployment Report

## Source-level checks completed
- Python `compileall` passed for `backend/app`.
- Pydantic email validation was tested for normal emails and the demo `.local` domain.
- Invalid email input is rejected by schema validation.
- Frontend code was reviewed for FastAPI validation-error handling; error arrays/objects are converted to text before rendering.
- Added Vercel SPA fallback for React Router deep links.
- Added backend `/` and `/api/health` endpoints for smoke checks.

## Production issue fixed
The demo login email `patient@medschedule.local` was rejected by Pydantic `EmailStr` because `.local` is a special-use domain. That caused HTTP 422; the frontend then attempted to render the structured FastAPI validation error object and React crashed with error #31. The schema now explicitly allows `.local` demo domains while continuing to validate normal email addresses, and the frontend normalizes validation errors to strings.

## Runtime limitation
Full browser E2E and a production PostgreSQL integration test could not be executed in this build environment because the required frontend packages were not installed locally and `psycopg` was not available in the build runner. The deployed Render/Vercel environments should be smoke-tested after updating the repository.
