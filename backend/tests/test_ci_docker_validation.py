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

FRAUD_FRONTEND = (
    PROJECT_ROOT
    / "frontend-fraud"
)

RESUME_FRONTEND = (
    PROJECT_ROOT
    / "frontend-resume"
)

LEGACY_FRONTEND = (
    PROJECT_ROOT
    / "frontend"
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
    ) == 4

    for service_name in (
        "db",
        "backend",
        "fraud-frontend",
        "resume-frontend",
    ):
        assert (
            f"\n  {service_name}:\n"
            in source
        )


def test_compose_uses_separate_frontend_ports():
    source = read_text(
        COMPOSE_FILE
    )

    assert '"5173:80"' in source
    assert '"5174:80"' in source

    assert (
        "context: ./frontend-fraud"
        in source
    )

    assert (
        "context: ./frontend-resume"
        in source
    )


def test_frontends_use_multistage_builds():
    for frontend in (
        FRAUD_FRONTEND,
        RESUME_FRONTEND,
    ):
        source = read_text(
            frontend / "Dockerfile"
        )

        assert (
            "FROM node:24.15-alpine "
            "AS build"
            in source
        )

        assert (
            "FROM nginx:1.27-alpine "
            "AS runtime"
            in source
        )

        assert "npm run build" in source

        assert (
            "COPY --from=build "
            "/app/dist"
            in source
        )


def test_frontend_builds_use_lockfiles():
    for frontend in (
        FRAUD_FRONTEND,
        RESUME_FRONTEND,
    ):
        source = read_text(
            frontend / "Dockerfile"
        )

        assert "package-lock.json" in source
        assert "npm ci" in source


def test_frontend_nginx_supports_spa_api_and_websockets():
    for frontend in (
        FRAUD_FRONTEND,
        RESUME_FRONTEND,
    ):
        source = read_text(
            frontend / "nginx.conf"
        )

        assert (
            "try_files $uri $uri/ "
            "/index.html;"
            in source
        )

        assert "location /api/" in source

        assert (
            "proxy_pass "
            "http://backend:8000;"
            in source
        )

        assert (
            "proxy_set_header Upgrade"
            in source
        )

        assert (
            "location = /health"
            in source
        )


def test_ci_has_docker_smoke_job():
    source = read_text(
        CI_WORKFLOW
    )

    assert "docker-smoke:" in source

    assert (
        "name: Docker separated "
        "frontends smoke test"
        in source
    )

    assert (
        "docker compose config --quiet"
        in source
    )

    assert (
        "docker compose build --pull"
        in source
    )

    assert (
        "docker compose up -d "
        "--wait --wait-timeout 180"
        in source
    )


def test_ci_verifies_backend_and_both_frontends():
    source = read_text(
        CI_WORKFLOW
    )

    assert (
        "http://localhost:8000/health"
        in source
    )

    assert (
        "Verify fraud frontend response"
        in source
    )

    assert (
        "http://localhost:5173/"
        in source
    )

    assert (
        "Verify resume frontend response"
        in source
    )

    assert (
        "http://localhost:5174/"
        in source
    )

    assert (
        'data.get("status") != "healthy"'
        in source
    )

    assert (
        'data.get("database") != '
        '"healthy"'
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


def test_legacy_combined_frontend_is_removed():
    assert not LEGACY_FRONTEND.exists()

    compose = read_text(
        COMPOSE_FILE
    )

    assert (
        "\n  frontend:\n"
        not in compose
    )

    assert (
        "context: ./frontend\n"
        not in compose
    )
