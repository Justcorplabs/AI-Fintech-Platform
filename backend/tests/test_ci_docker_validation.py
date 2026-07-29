from pathlib import Path


PROJECT_ROOT = (
    Path(__file__).resolve().parents[2]
)
CI_WORKFLOW = (
    PROJECT_ROOT
    / ".github"
    / "workflows"
    / "ci.yml"
)
COMPOSE_FILE = (
    PROJECT_ROOT
    / "docker-compose.yml"
)
FRONTEND_DOCKERFILE = (
    PROJECT_ROOT
    / "frontend"
    / "Dockerfile"
)
FRONTEND_NGINX = (
    PROJECT_ROOT
    / "frontend"
    / "nginx.conf"
)


def read_text(
    path: Path,
) -> str:
    return path.read_text(
        encoding="utf-8"
    )


def test_compose_does_not_require_local_env_file():
    source = read_text(
        COMPOSE_FILE
    )

    assert "env_file:" not in source
    assert (
        "SECRET_KEY: "
        "docker-development-secret-key"
        in source
    )


def test_compose_defines_all_service_health_checks():
    source = read_text(
        COMPOSE_FILE
    )

    assert source.count(
        "healthcheck:"
    ) == 3
    assert (
        "condition: service_healthy"
        in source
    )


def test_compose_uses_production_frontend_port():
    source = read_text(
        COMPOSE_FILE
    )

    assert '"5173:80"' in source


def test_frontend_uses_multistage_build():
    source = read_text(
        FRONTEND_DOCKERFILE
    )

    assert (
        "FROM node:20-alpine AS build"
        in source
    )
    assert (
        "FROM nginx:1.27-alpine AS runtime"
        in source
    )
    assert "npm run build" in source
    assert (
        "COPY --from=build /app/dist"
        in source
    )


def test_frontend_build_supports_lockfile_or_fallback():
    source = read_text(
        FRONTEND_DOCKERFILE
    )

    assert "package-lock.json" in source
    assert "npm ci" in source
    assert "npm install" in source


def test_nginx_supports_spa_and_api_proxy():
    source = read_text(
        FRONTEND_NGINX
    )

    assert (
        "try_files $uri $uri/ /index.html;"
        in source
    )
    assert "location /api/" in source
    assert (
        "proxy_pass http://backend:8000/api/;"
        in source
    )


def test_ci_has_docker_smoke_job():
    source = read_text(
        CI_WORKFLOW
    )

    assert "docker-smoke:" in source
    assert (
        "name: Docker full-stack smoke test"
        in source
    )
    assert (
        "docker compose build --pull"
        in source
    )
    assert "docker compose up -d" in source


def test_ci_verifies_backend_and_frontend():
    source = read_text(
        CI_WORKFLOW
    )

    assert (
        "http://localhost:8000/health"
        in source
    )
    assert (
        "http://localhost:5173/"
        in source
    )
    assert (
        'data.get("status") != "healthy"'
        in source
    )
    assert (
        'data.get("database") != "healthy"'
        in source
    )


def test_ci_always_collects_logs_and_cleans_up():
    source = read_text(
        CI_WORKFLOW
    )

    assert (
        "docker compose logs --no-color"
        in source
    )
    assert (
        "docker compose down "
        "--volumes --remove-orphans"
        in source
    )
    assert source.count(
        "if: always()"
    ) >= 3


def test_python_runtime_supports_declared_dependencies():
    workflow_source = read_text(
        CI_WORKFLOW
    )

    docker_source = read_text(
        PROJECT_ROOT
        / "backend"
        / "Dockerfile"
    )

    assert (
        workflow_source.count(
            'python-version: "3.12"'
        )
        == 2
    )

    assert (
        "FROM python:3.12-slim"
        in docker_source
    )

