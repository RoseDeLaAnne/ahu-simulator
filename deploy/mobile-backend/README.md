# Mobile backend deployment (HTTPS + CORS)

This deployment profile is intended for Android Capacitor clients that load the dashboard from a stable HTTPS endpoint.

## What this stack does

- runs AHU API/dashboard in Docker (`api` service);
- exposes public HTTPS via Caddy (`caddy` service);
- enables strict response security headers at the edge;
- applies FastAPI host/CORS policy via environment overrides.

## Prerequisites

- DNS record for `MOBILE_PUBLIC_HOST` points to this server;
- ports `80` and `443` are reachable from the internet;
- Docker Desktop / Docker Engine is installed.

## First start

1. Copy [.env.example](.env.example) to `deploy/mobile-backend/.env` and fill real values.
2. Start services from the project root:

```powershell
docker compose --env-file deploy/mobile-backend/.env -f deploy/mobile-backend/docker-compose.mobile.yml up -d --build
```

3. Verify endpoints:

- `https://<MOBILE_PUBLIC_HOST>/health`
- `https://<MOBILE_PUBLIC_HOST>/dashboard`
- `https://<MOBILE_PUBLIC_HOST>/docs`

## Stop

```powershell
docker compose --env-file deploy/mobile-backend/.env -f deploy/mobile-backend/docker-compose.mobile.yml down
```

## Notes

- This profile uses `config/defaults.mobile.yaml` via `AHU_SIMULATOR_SETTINGS_FILE`.
- CORS and trusted hosts are expected to be provided from `.env`.
- TLS is terminated at Caddy; Uvicorn runs behind proxy with `--proxy-headers`.
