from pathlib import Path


def test_alembic_env_does_not_emit_debug_prints():
    env_content = Path("alembic/env.py").read_text()

    assert "print(" not in env_content
    assert "ALEMBIC DEBUG" not in env_content


def test_authorization_description_typo_is_migrated_forward():
    migration_content = Path(
        "alembic/versions/c7a1b9e5d4f2_rename_authorization_description_columns.py"
    ).read_text()

    assert "descpription" in migration_content
    assert "description" in migration_content
    assert "rename_column" in migration_content


def test_authorization_resources_are_migrated_forward():
    migration_content = Path(
        "alembic/versions/d9a7c3f2b6e1_add_authorization_resources.py"
    ).read_text()

    assert "authorization_resources" in migration_content
    assert "resource_id" in migration_content
    assert "permissions" in migration_content
