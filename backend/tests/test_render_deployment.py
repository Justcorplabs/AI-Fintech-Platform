from pathlib import Path


PROJECT_ROOT = (
    Path(__file__).resolve().parents[2]
)

BLUEPRINT = PROJECT_ROOT / "render.yaml"
RENDER_DOCKERFILE = (
    PROJECT_ROOT
    / "backend"
    / "Dockerfile.render"
)
ENTRYPOINT = (
    PROJECT_ROOT
    / "backend"
    / "entrypoint.sh"
)
ROOT_DOCKERIGNORE = (
    PROJECT_ROOT
    / ".dockerignore"
)


def read_text(path: Path) -> str:
    return path.read_text(
        encoding="utf-8-sig"
    )


def test_render_blueprint_defines_complete_platform():
    source = read_text(BLUEPRINT)

    assert (
        "name: justcorplabs-ai-fintech-api"
        in source
    )

    assert (
        "name: justcorplabs-fraud-intelligence"
        in source
    )

    assert (
        "name: justcorplabs-resume-intelligence"
        in source
    )

    assert (
        "name: justcorplabs-ai-fintech-db"
        in source
    )

    assert source.count(
        "runtime: static"
    ) == 2

    assert (
        "runtime: docker"
        in source
    )


def test_render_blueprint_uses_managed_secrets_and_database():
    source = read_text(BLUEPRINT)

    assert "generateValue: true" in source
    assert "sync: false" in source
    assert "fromDatabase:" in source
    assert "property: connectionString" in source

    assert (
        "docker-development-secret-key"
        not in source
    )

    assert (
        "postgres:password@"
        not in source
    )


def test_render_blueprint_uses_production_settings():
    source = read_text(BLUEPRINT)

    assert "value: production" in source
    assert "healthCheckPath: /health" in source
    assert "autoDeployTrigger: checksPass" in source

    assert (
        "justcorplabs-fraud-intelligence."
        "onrender.com"
        in source
    )

    assert (
        "justcorplabs-resume-intelligence."
        "onrender.com"
        in source
    )


def test_render_static_sites_receive_backend_url():
    source = read_text(BLUEPRINT)

    assert source.count(
        "key: VITE_API_BASE_URL"
    ) == 2

    assert source.count(
        "envVarKey: RENDER_EXTERNAL_URL"
    ) == 2

    assert source.count(
        "destination: /index.html"
    ) == 2


def test_render_backend_image_contains_model_bundle():
    source = read_text(
        RENDER_DOCKERFILE
    )

    required_artifacts = (
        "champion_lightgbm_model.pkl",
        "champion_isotonic_calibrator.pkl",
        "shap_explainer.pkl",
        "model_features.pkl",
        "model_defaults.pkl",
        "label_encoders.pkl",
    )

    for artifact in required_artifacts:
        assert artifact in source


def test_render_entrypoint_uses_platform_port():
    source = read_text(ENTRYPOINT)

    assert 'PORT="${PORT:-8000}"' in source
    assert '--port "$PORT"' in source


def test_render_docker_context_excludes_raw_data():
    source = read_text(
        ROOT_DOCKERIGNORE
    )

    assert source.startswith("**")
    assert "!backend/app/**" in source
    assert "!backend/alembic/**" in source
    assert "!ml/models/shap_explainer.pkl" in source
    assert (
        "!data/processed/label_encoders.pkl"
        in source
    )


def test_frontends_support_external_api_origin():
    for frontend in (
        "frontend-fraud",
        "frontend-resume",
    ):
        source = read_text(
            PROJECT_ROOT
            / frontend
            / "src"
            / "services"
            / "httpClient.js"
        )

        assert (
            "import.meta.env.VITE_API_BASE_URL"
            in source
        )

        assert "baseURL: apiBaseURL" in source


def test_fraud_websocket_supports_external_api_origin():
    source = read_text(
        PROJECT_ROOT
        / "frontend-fraud"
        / "src"
        / "pages"
        / "Dashboard.jsx"
    )

    assert (
        "import.meta.env.VITE_API_BASE_URL"
        in source
    )

    assert "websocketOrigin" in source
    assert '.replace(/^https:/, "wss:")' in source
