# Deployment

This project is split for separate hosting:

- `frontend/`: React app for Vercel.
- `backend/`: Django API for Railway.

## Vercel

Create a Vercel project with these settings:

- Root Directory: `frontend`
- Build Command: `npm run build`
- Output Directory: `build`

Set these environment variables after Railway gives you the backend URL:

```text
REACT_APP_API_BASE_URL=https://kwetucare-foundation-production.up.railway.app/api
REACT_APP_WS_URL=wss://kwetucare-foundation-production.up.railway.app/ws/updates/
```

## Railway

Create a Railway service from this repository with:

- Root Directory: leave empty, or set it to `/`
- Config File Path: `/railway.json`
- Start Command: Railway can use `railway.json` or `nixpacks.toml`.

There is also a backend-only config in `backend/railway.json` if you prefer setting Railway's root directory to `/backend`.

Add a Railway PostgreSQL database, then set these backend environment variables:

```text
DATABASE_URL=<Railway PostgreSQL DATABASE_URL>
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=<a long random secret>
DJANGO_ALLOWED_HOSTS=kwetucare-foundation-production.up.railway.app
CORS_ALLOWED_ORIGINS=https://kwetu-care-foundation-i6vf7j1wj-imbukwa1s-projects.vercel.app
CSRF_TRUSTED_ORIGINS=https://kwetu-care-foundation-i6vf7j1wj-imbukwa1s-projects.vercel.app
FRONTEND_URL=https://kwetu-care-foundation-i6vf7j1wj-imbukwa1s-projects.vercel.app
BYPASS_USER_APPROVAL=false
ADMIN_NOTIFICATION_EMAIL=kwetucarefoundation@gmail.com
EMAIL_BACKEND=core.email_backend.IPv4GmailSMTPEmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=kwetucarefoundation@gmail.com
EMAIL_HOST_PASSWORD=<Gmail App Password>
DEFAULT_FROM_EMAIL=kwetucarefoundation@gmail.com
EMAIL_VERIFICATION_EXPIRY_MINUTES=10
EMAIL_VERIFICATION_MAX_ATTEMPTS=3
```

The Gmail password must be a Gmail App Password for `kwetucarefoundation@gmail.com`, not the normal mailbox password.
The custom email backend still uses Django's SMTP email backend, but forces IPv4 so Railway does not fail when `smtp.gmail.com` resolves to IPv6 first.

Current public URLs:

```text
Backend: https://kwetucare-foundation-production.up.railway.app
Frontend: https://kwetu-care-foundation-i6vf7j1wj-imbukwa1s-projects.vercel.app
```

For local frontend development, run the backend on port `8080`; `frontend/package.json` still proxies API requests to `http://127.0.0.1:8080`.
