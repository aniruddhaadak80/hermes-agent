"""Regression tests for #158256: a gateway running from a custom HERMES_HOME must
tick and probe its own home, not ``~/.hermes/profiles/custom``.
"""

from pathlib import Path
from unittest.mock import patch

from gateway.run import _cron_tick_profile_homes


def _homes(active: str, custom_home: Path, profiles_root: Path):
    served = [("default", profiles_root.parent)]
    with (
        patch("gateway.run._multiplex_profile_homes", return_value=served),
        patch("hermes_cli.profiles.get_active_profile_name", return_value=active),
        patch(
            "hermes_cli.profiles.get_profile_dir", return_value=profiles_root / active
        ),
        patch("gateway.run.get_hermes_home", return_value=custom_home),
    ):
        return _cron_tick_profile_homes(object())


def test_custom_active_home_uses_the_gateway_own_home(tmp_path):
    custom_home = tmp_path / "custom-home"
    profiles_root = tmp_path / ".hermes" / "profiles"

    homes = _homes("custom", custom_home, profiles_root)

    assert ("custom", custom_home) in homes
    assert profiles_root / "custom" not in [home for _name, home in homes]


def test_named_active_profile_still_uses_its_profile_dir(tmp_path):
    custom_home = tmp_path / "custom-home"
    profiles_root = tmp_path / ".hermes" / "profiles"

    homes = _homes("work", custom_home, profiles_root)

    assert ("work", profiles_root / "work") in homes
    assert custom_home not in [home for _name, home in homes]


def test_default_active_home_is_not_duplicated(tmp_path):
    custom_home = tmp_path / "custom-home"
    profiles_root = tmp_path / ".hermes" / "profiles"
    default_home = profiles_root.parent

    with (
        patch(
            "gateway.run._multiplex_profile_homes",
            return_value=[("default", default_home)],
        ),
        patch("hermes_cli.profiles.get_active_profile_name", return_value="default"),
        patch("hermes_cli.profiles.get_profile_dir", return_value=default_home),
        patch("gateway.run.get_hermes_home", return_value=custom_home),
    ):
        homes = _cron_tick_profile_homes(object())

    assert homes == [("default", default_home)]
