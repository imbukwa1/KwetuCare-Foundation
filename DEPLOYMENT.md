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
REACT_APP_API_BASE_URL=https://your-railway-app.up.railway.app/api
REACT_APP_WS_URL=wss://your-railway-app.up.railway.app/ws/updates/
```

## Railway

Create a Railway service from this repository with:

- Root Directory: `backend`
- Start Command: Railway can use `backend/Procfile`.

Add a Railway PostgreSQL database, then set these backend environment variables:

```text
DATABASE_URL=<Railway PostgreSQL DATABASE_URL>
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=<a long random secret>
DJANGO_ALLOWED_HOSTS=your-railway-app.up.railway.app
CORS_ALLOWED_ORIGINS=https://your-vercel-app.vercel.app
CSRF_TRUSTED_ORIGINS=https://your-vercel-app.vercel.app
BYPASS_USER_APPROVAL=false
```

For local frontend development, run the backend on port `8000`; `frontend/package.json` still proxies API requests to `http://127.0.0.1:8000`.
