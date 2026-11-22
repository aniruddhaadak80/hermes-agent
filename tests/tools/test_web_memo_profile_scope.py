"""Regression tests for #158297: the in-memory web_search memo and its single-flight
locks must be scoped to the active profile's home on a multiplexed gateway.
"""

from unittest.mock import patch

import tools.web_result_cache as wrc
from tools.web_result_cache import SearchMemo


def _response():
    return {
        "success": True,
        "data": {"web": [{"title": "t", "url": "https://e.com/1"}]},
    }


def _in_home(home: str):
    return patch.object(wrc, "hermes_home_key", return_value=home)


def test_memo_key_includes_the_profile_home():
    with _in_home("home-a"):
        a = SearchMemo._key("provider", "some query", 5)
    with _in_home("home-b"):
        b = SearchMemo._key("provider", "some query", 5)

    assert a != b
    with _in_home("home-a"):
        assert SearchMemo._key("provider", "some query", 5) == a


def test_lookup_does_not_share_a_response_across_profiles():
    memo = SearchMemo()
    with _in_home("home-a"):
        memo.store("provider", "shared query", 5, _response())
        assert memo.lookup("provider", "shared query", 5)["success"]
    with _in_home("home-b"):
        assert memo.lookup("provider", "shared query", 5) is None


def test_flight_locks_are_separate_per_profile():
    memo = SearchMemo()
    with _in_home("home-a"):
        a1 = memo.flight_lock("provider", "q", 5)
        a2 = memo.flight_lock("provider", "q", 5)
    with _in_home("home-b"):
        b = memo.flight_lock("provider", "q", 5)

    assert a1 is a2
    assert a1 is not b
