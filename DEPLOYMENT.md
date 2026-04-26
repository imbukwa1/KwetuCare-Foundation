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

- Root Directory: `backend`
- Config File Path: `/backend/railway.json`
- Start Command: Railway can use `backend/railway.json`, `backend/nixpacks.toml`, or `backend/Procfile`.

Add a Railway PostgreSQL database, then set these backend environment variables:

```text
DATABASE_URL=<Railway PostgreSQL DATABASE_URL>
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=<a long random secret>
DJANGO_ALLOWED_HOSTS=kwetucare-foundation-production.up.railway.app
CORS_ALLOWED_ORIGINS=https://kwetu-care-foundation-i6vf7j1wj-imbukwa1s-projects.vercel.app
CSRF_TRUSTED_ORIGINS=https://kwetu-care-foundation-i6vf7j1wj-imbukwa1s-projects.vercel.app
BYPASS_USER_APPROVAL=false
```

Current public URLs:

```text
Backend: https://kwetucare-foundation-production.up.railway.app
Frontend: https://kwetu-care-foundation-i6vf7j1wj-imbukwa1s-projects.vercel.app
```

For local frontend development, run the backend on port `8000`; `frontend/package.json` still proxies API requests to `http://127.0.0.1:8000`.
