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


def test_frontends_use_patched_dependency_versions():
    for frontend in (
        FRAUD_FRONTEND,
        RESUME_FRONTEND,
    ):
        package = read_package(frontend)

        assert (
            package["dependencies"][
                "react-router"
            ]
            == "8.3.0"
        )

        assert (
            package["devDependencies"]["vite"]
            == "8.1.5"
        )

        assert (
            package["devDependencies"][
                "@vitejs/plugin-react"
            ]
            == "6.0.4"
        )


def test_frontend_docker_builds_use_supported_node():
    for frontend in (
        FRAUD_FRONTEND,
        RESUME_FRONTEND,
    ):
        dockerfile = read_text(
            frontend / "Dockerfile"
        )

        assert (
            "FROM node:24.15-alpine AS build"
            in dockerfile
        )


def test_frontends_use_react_nineteen():
    for frontend in (
        FRAUD_FRONTEND,
        RESUME_FRONTEND,
    ):
        package = read_package(frontend)

        assert (
            package["dependencies"]["react"]
            == "19.2.8"
        )

        assert (
            package["dependencies"]["react-dom"]
            == "19.2.8"
        )


def test_frontends_do_not_depend_on_react_router_dom():
    for frontend in (
        FRAUD_FRONTEND,
        RESUME_FRONTEND,
    ):
        package = read_package(frontend)

        assert (
            package["dependencies"]["react-router"]
            == "8.3.0"
        )

        assert (
            "react-router-dom"
            not in package["dependencies"]
        )


def test_frontends_exclude_cross_domain_source_files():
    forbidden_fraud_paths = [
        FRAUD_FRONTEND
        / "src"
        / "components"
        / "recruitment",
        FRAUD_FRONTEND
        / "src"
        / "pages"
        / "Recruitment.jsx",
        FRAUD_FRONTEND
        / "src"
        / "pages"
        / "ResumeReviewer.jsx",
    ]

    forbidden_resume_paths = [
        RESUME_FRONTEND
        / "src"
        / "components"
        / "fraud",
        RESUME_FRONTEND
        / "src"
        / "pages"
        / "Dashboard.jsx",
        RESUME_FRONTEND
        / "src"
        / "pages"
        / "Fraud.jsx",
        RESUME_FRONTEND
        / "src"
        / "pages"
        / "Transactions.jsx",
        RESUME_FRONTEND
        / "src"
        / "pages"
        / "Investigation.jsx",
        RESUME_FRONTEND
        / "src"
        / "pages"
        / "Analytics.jsx",
        RESUME_FRONTEND
        / "src"
        / "pages"
        / "Reports.jsx",
        RESUME_FRONTEND
        / "src"
        / "pages"
        / "DriftMonitoring.jsx",
        RESUME_FRONTEND
        / "src"
        / "pages"
        / "Settings.jsx",
    ]

    for forbidden_path in (
        forbidden_fraud_paths
        + forbidden_resume_paths
    ):
        assert not forbidden_path.exists()


def test_frontends_retain_their_domain_pages():
    required_fraud_pages = [
        "Dashboard.jsx",
        "Fraud.jsx",
        "Transactions.jsx",
        "Investigation.jsx",
        "Analytics.jsx",
        "Reports.jsx",
        "DriftMonitoring.jsx",
        "Settings.jsx",
    ]

    required_resume_pages = [
        "Recruitment.jsx",
        "ResumeReviewer.jsx",
    ]

    for page_name in required_fraud_pages:
        assert (
            FRAUD_FRONTEND
            / "src"
            / "pages"
            / page_name
        ).is_file()

    for page_name in required_resume_pages:
        assert (
            RESUME_FRONTEND
            / "src"
            / "pages"
            / page_name
        ).is_file()

