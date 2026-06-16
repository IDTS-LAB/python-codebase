import subprocess


def test_make_help_uses_target_prefixes():
    result = subprocess.run(
        ["make", "help"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "[make:help]" in result.stdout
    assert "[make:test]" in result.stdout
    assert "[make:check]" in result.stdout
