# Docker deployment and smoke testing

The repository contains a three-service Compose stack:

- PostgreSQL 15;
- FastAPI backend;
- React/Vite frontend served by Nginx.

## Local prerequisites

Docker Desktop or another Docker Engine installation must provide:

```bash
docker --version
docker compose version
docker info
```

If these commands are unavailable, use the GitHub Actions Docker smoke test.

## Build and start

Run from the repository root:

```bash
docker compose build
docker compose up -d
docker compose ps
```

The backend entrypoint applies Alembic migrations before starting Uvicorn.
The frontend starts only after the backend health check succeeds.

## Health verification

```bash
curl --fail http://localhost:8000/health
curl --fail http://localhost:5173/
```

Expected backend fields:

```json
{
  "status": "healthy",
  "database": "healthy"
}
```

## Logs and shutdown

```bash
docker compose logs db
docker compose logs backend
docker compose logs frontend
docker compose down --volumes --remove-orphans
```

Using `--volumes` removes the disposable PostgreSQL volume. Do not use it
against an environment whose database volume must be retained.

## Environment configuration

The base Compose file contains development-only values required for a
self-contained smoke test. Never reuse its database password or JWT secret in
production. Production deployments must provide secrets through their
deployment platform or secret manager.

The frontend Nginx server proxies `/api/` requests to the backend service.
Frontend API calls should use a relative `/api` base path for this stack.

## CI validation

The Docker CI job validates Compose, builds both images, starts the stack,
waits for healthy services, verifies backend and frontend responses, captures
diagnostics, and always removes containers, networks, and volumes.
