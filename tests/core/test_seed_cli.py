from pathlib import Path

from src.core.config.setting import Settings


def test_makefile_exposes_seed_command():
    makefile = Path("Makefile").read_text()

    assert "seed:" in makefile
    assert "[make:seed]" in makefile
    assert "scripts/seed.py" in makefile


def test_seed_script_uses_seed_runner():
    script = Path("scripts/seed.py").read_text()

    assert "sys.path.insert" in script
    assert "run_seeders" in script
    assert "seed:user" in script


def test_env_example_documents_seed_admin_settings():
    env_example = Path(".env.example").read_text()

    assert "SEED_ADMIN_EMAIL=" in env_example
    assert "SEED_ADMIN_PASSWORD=" in env_example
    assert "SEED_ADMIN_USERNAME=admin" in env_example
    assert "SEED_ADMIN_FULLNAME=System Administrator" in env_example
    assert "SEED_DEVELOPMENT_USERS_PASSWORD=" in env_example


def test_seed_development_users_password_has_no_default_secret():
    settings = Settings(_env_file=None)

    assert settings.SEED_DEVELOPMENT_USERS_PASSWORD == ""
