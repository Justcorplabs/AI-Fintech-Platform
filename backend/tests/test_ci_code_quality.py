from pathlib import Path


PROJECT_ROOT = (
    Path(__file__).resolve().parents[2]
)
BACKEND_ROOT = PROJECT_ROOT / "backend"
CI_WORKFLOW = (
    PROJECT_ROOT
    / ".github"
    / "workflows"
    / "ci.yml"
)


def read_text(
    path: Path,
) -> str:
    return path.read_text(
        encoding="utf-8"
    )


def test_ci_has_backend_quality_job():
    source = read_text(
        CI_WORKFLOW
    )

    assert "backend-quality:" in source
    assert (
        "name: Backend code quality"
        in source
    )


def test_ci_installs_development_requirements():
    source = read_text(
        CI_WORKFLOW
    )

    assert (
        "pip install -r requirements-dev.txt"
        in source
    )
    assert (
        "backend/requirements-dev.txt"
        in source
    )


def test_ci_enforces_ruff_and_bandit():
    source = read_text(
        CI_WORKFLOW
    )

    assert (
        "python -m ruff check "
        "app tests alembic"
        in source
    )
    assert (
        "python -m bandit "
        "-r app -q -lll -iii"
        in source
    )


def test_black_is_advisory():
    source = read_text(
        CI_WORKFLOW
    )

    step_start = source.index(
        "- name: Report Black "
        "formatting drift"
    )
    next_step = source.index(
        "- name: Audit runtime "
        "dependencies"
    )

    black_step = source[
        step_start:next_step
    ]

    assert (
        "continue-on-error: true"
        in black_step
    )
    assert (
        "python -m black --check "
        "app tests alembic"
        in black_step
    )


def test_dependency_audit_is_advisory_and_scoped():
    source = read_text(
        CI_WORKFLOW
    )

    step_start = source.index(
        "- name: Audit runtime "
        "dependencies"
    )
    next_step = source.index(
        "- name: Upload dependency "
        "audit report"
    )

    audit_step = source[
        step_start:next_step
    ]

    assert (
        "continue-on-error: true"
        in audit_step
    )
    assert "-r requirements.txt" in audit_step
    assert (
        "--output pip-audit-report.json"
        in audit_step
    )


def test_dependency_audit_report_is_uploaded():
    source = read_text(
        CI_WORKFLOW
    )

    assert (
        "uses: actions/upload-artifact@v4"
        in source
    )
    assert (
        "path: backend/"
        "pip-audit-report.json"
        in source
    )
    assert "retention-days: 14" in source


def test_development_requirements_define_tools():
    source = read_text(
        BACKEND_ROOT
        / "requirements-dev.txt"
    )

    assert "-r requirements.txt" not in source
    assert "black>=24.4" in source
    assert "ruff==0.16.0" in source
    assert "bandit==1.9.4" in source
    assert "pip-audit==2.10.1" in source


def test_runtime_requirements_exclude_black():
    source = read_text(
        BACKEND_ROOT
        / "requirements.txt"
    )

    assert "black" not in source.lower()


def test_runtime_requirements_include_email_validator():
    source = read_text(
        BACKEND_ROOT
        / "requirements.txt"
    ).lower()

    assert (
        "email-validator"
        in source
    )

