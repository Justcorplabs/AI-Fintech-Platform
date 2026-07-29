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


def read_ci_workflow() -> str:
    return CI_WORKFLOW.read_text(
        encoding="utf-8"
    )


def test_ci_targets_main_and_dev():
    source = read_ci_workflow()

    assert (
        source.count(
            "branches: [main, dev]"
        )
        == 2
    )

    assert "develop" not in source


def test_ci_exposes_and_health_checks_postgres():
    source = read_ci_workflow()

    assert "POSTGRES_DB: ai_fintech_test" in source
    assert "- 5432:5432" in source
    assert (
        "pg_isready -U postgres "
        "-d ai_fintech_test"
    ) in source


def test_ci_disables_runtime_table_creation():
    source = read_ci_workflow()

    assert (
        'CREATE_DATABASE_TABLES: "false"'
        in source
    )


def test_ci_validates_single_alembic_head():
    source = read_ci_workflow()

    assert "scripts.get_heads()" in source
    assert "len(heads) != 1" in source


def test_ci_runs_complete_migration_cycle():
    source = read_ci_workflow()

    first_upgrade = source.index(
        "python -m alembic upgrade head"
    )
    downgrade = source.index(
        "python -m alembic downgrade base"
    )
    second_upgrade = source.rindex(
        "python -m alembic upgrade head"
    )
    tests = source.index(
        "python -m pytest tests -q"
    )

    assert (
        first_upgrade
        < downgrade
        < second_upgrade
        < tests
    )


def test_ci_checks_schema_drift_twice():
    source = read_ci_workflow()

    assert (
        source.count(
            "python -m alembic check"
        )
        == 2
    )


def test_ci_verifies_enum_cleanup():
    source = read_ci_workflow()

    assert "applicationstatus" in source
    assert "fraudstatus" in source
    assert "userrole" in source
    assert (
        "Downgrade cleanup verified."
        in source
    )
