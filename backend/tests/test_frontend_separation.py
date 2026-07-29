import json
from pathlib import Path


PROJECT_ROOT = (
    Path(__file__).resolve().parents[2]
)

FRAUD_FRONTEND = (
    PROJECT_ROOT
    / "frontend-fraud"
)

RESUME_FRONTEND = (
    PROJECT_ROOT
    / "frontend-resume"
)


def read_text(path: Path) -> str:
    return path.read_text(
        encoding="utf-8-sig"
    )


def read_package(path: Path) -> dict:
    return json.loads(
        read_text(
            path / "package.json"
        )
    )


def test_separate_frontend_directories_exist():
    assert FRAUD_FRONTEND.is_dir()
    assert RESUME_FRONTEND.is_dir()


def test_frontends_have_distinct_package_names():
    fraud_package = read_package(
        FRAUD_FRONTEND
    )

    resume_package = read_package(
        RESUME_FRONTEND
    )

    assert fraud_package["name"] == (
        "justcorp-fraud-frontend"
    )

    assert resume_package["name"] == (
        "justcorp-resume-reviewer-frontend"
    )

    assert (
        fraud_package["name"]
        != resume_package["name"]
    )


def test_frontends_use_distinct_development_ports():
    fraud_vite = read_text(
        FRAUD_FRONTEND
        / "vite.config.js"
    )

    resume_vite = read_text(
        RESUME_FRONTEND
        / "vite.config.js"
    )

    assert "port: 5173" in fraud_vite
    assert "port: 5174" in resume_vite


def test_fraud_router_excludes_recruitment_routes():
    source = read_text(
        FRAUD_FRONTEND
        / "src"
        / "App.jsx"
    )

    assert 'path="/fraud"' in source
    assert 'path="/transactions"' in source

    assert 'path="/recruitment"' not in source
    assert 'path="/resume-reviewer"' not in source


def test_resume_router_excludes_fraud_routes():
    source = read_text(
        RESUME_FRONTEND
        / "src"
        / "App.jsx"
    )

    assert 'path="/resume-reviewer"' in source
    assert 'path="/recruitment"' in source

    assert 'path="/fraud"' not in source
    assert 'path="/transactions"' not in source
