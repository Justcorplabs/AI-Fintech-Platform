from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


BACKEND_ROOT = (
    Path(__file__).resolve().parents[1]
)
PROJECT_ROOT = BACKEND_ROOT.parent


def read_backend_file(
    relative_path: str,
) -> str:
    return (
        BACKEND_ROOT
        / relative_path
    ).read_text(
        encoding="utf-8"
    )


def test_alembic_has_single_expected_head():
    config = Config(
        str(
            BACKEND_ROOT
            / "alembic.ini"
        )
    )
    config.set_main_option(
        "script_location",
        str(
            BACKEND_ROOT
            / "alembic"
        ),
    )

    scripts = ScriptDirectory.from_config(
        config
    )

    assert scripts.get_heads() == [
        "e1c4b9a7f2d8"
    ]


def test_alembic_revision_chain_is_linear():
    config = Config(
        str(
            BACKEND_ROOT
            / "alembic.ini"
        )
    )
    config.set_main_option(
        "script_location",
        str(
            BACKEND_ROOT
            / "alembic"
        ),
    )

    scripts = ScriptDirectory.from_config(
        config
    )

    revisions = list(
        scripts.walk_revisions(
            base="base",
            head="heads",
        )
    )

    assert [
        revision.revision
        for revision in revisions
    ] == [
        "e1c4b9a7f2d8",
        "b7dad0f55492",
    ]

    assert (
        revisions[0].down_revision
        == "b7dad0f55492"
    )
    assert (
        revisions[1].down_revision
        is None
    )


def test_fastapi_startup_does_not_create_tables():
    source = read_backend_file(
        "app/main.py"
    )

    assert "create_all" not in source
    assert "drop_all" not in source
    assert (
        "from app.db.database "
        "import Base"
    ) not in source


def test_database_table_creation_is_disabled_by_default():
    source = read_backend_file(
        "app/core/config.py"
    )

    assert (
        "CREATE_DATABASE_TABLES: "
        "bool = False"
    ) in source


def test_entrypoint_migrates_before_starting_api():
    source = read_backend_file(
        "entrypoint.sh"
    )

    migration_position = source.index(
        "python -m alembic upgrade head"
    )
    server_position = source.index(
        "exec uvicorn"
    )

    assert migration_position < server_position
    assert "set -eu" in source


def test_dockerfile_uses_migration_entrypoint():
    source = read_backend_file(
        "Dockerfile"
    )

    assert (
        'ENTRYPOINT ["sh", "/app/entrypoint.sh"]'
        in source
    )
    assert "--reload" not in source


def test_compose_waits_for_database_health():
    source = (
        PROJECT_ROOT
        / "docker-compose.yml"
    ).read_text(
        encoding="utf-8"
    )

    assert "healthcheck:" in source
    assert (
        "condition: service_healthy"
        in source
    )
    assert (
        'CREATE_DATABASE_TABLES: "false"'
        in source
    )


def test_example_environment_disables_table_creation():
    source = read_backend_file(
        ".env.example"
    )

    assert (
        "CREATE_DATABASE_TABLES=False"
        in source
    )



def test_shell_scripts_are_forced_to_lf():
    source = read_backend_file(
        ".gitattributes"
    )

    assert "*.sh text eol=lf" in source
