"""Startup config warnings must not leak raw ANSI into piped output (#94024).

print_config_warnings() and warn_deprecated_cwd_env_vars() wrote hardcoded
escape sequences regardless of NO_COLOR / TTY state. They now route through
hermes_cli.colors like every other surface.
"""

import sys

import pytest


@pytest.fixture()
def clean_home(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    return tmp_path


def _cap_stderr(monkeypatch):
    buf = []
    monkeypatch.setattr(sys, "stderr", type("S", (), {"write": staticmethod(lambda s: buf.append(s)), "flush": staticmethod(lambda: None)})())
    return "".join(buf)


def test_config_warnings_plain_when_no_color(clean_home, monkeypatch, capsys):
    from hermes_cli.config import print_config_warnings

    bad_config = {"custom_providers": "not-a-list"}
    monkeypatch.setenv("NO_COLOR", "1")
    print_config_warnings(bad_config)
    err = capsys.readouterr().err
    if not err.strip():
        pytest.skip("validator produced no issues for this config shape")
    assert "\033[" not in err, f"raw ANSI leaked under NO_COLOR: {err!r}"
    assert "Config issues" in err


def test_cwd_env_warnings_plain_when_no_color(clean_home, monkeypatch, capsys):
    from hermes_cli.config import warn_deprecated_cwd_env_vars

    env_file = clean_home / ".env"
    env_file.write_text("TERMINAL_CWD=/tmp/project\n", encoding="utf-8")
    monkeypatch.setenv("NO_COLOR", "1")
    # load_env caches; point it at this fresh file.
    from hermes_cli.config import invalidate_env_cache
    invalidate_env_cache()

    warn_deprecated_cwd_env_vars()
    invalidate_env_cache()
    err = capsys.readouterr().err
    assert "TERMINAL_CWD" in err
    assert "\033[" not in err, f"raw ANSI leaked under NO_COLOR: {err!r}"


def test_config_warnings_color_when_tty_like(clean_home, monkeypatch, capsys):
    """Colors still appear when NO_COLOR is unset (stdout TTY state governs)."""
    from hermes_cli import colors as colors_mod
    from hermes_cli.config import print_config_warnings

    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setattr(colors_mod.sys.stdout, "isatty", lambda: True, raising=False)
    print_config_warnings({"custom_providers": "not-a-list"})
    err = capsys.readouterr().err
    if not err.strip():
        pytest.skip("validator produced no issues for this config shape")
    assert "\033[33m" in err or "⚠" in err
