# Production fixes

- Allow controlled `.local` demo emails while keeping normal email validation.
- Normalize FastAPI/Pydantic validation errors to user-facing strings so React never renders an error object.
- Add Vercel SPA fallback so `/login`, `/patient`, `/doctor`, etc. survive direct loads.
- Add `/` and `/api/health` backend endpoints for service checks.
