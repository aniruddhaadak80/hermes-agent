"""Regression tests for #158111: affection words inside @-reference expansion
footers are app/context text, not words the user typed.
"""

from types import SimpleNamespace

from agent.turn_context import _emit_reaction


def _reactions(message) -> list[str]:
    got: list[str] = []
    _emit_reaction(SimpleNamespace(reaction_callback=got.append), message)
    return got


def test_attached_context_footer_does_not_trigger_a_heart():
    message = (
        "@url:https://example.com/actions/runs/1\n\n"
        "--- Attached Context ---\n\n"
        "Made with \u2764\ufe0f by humans.txt"
    )

    assert _reactions(message) == []


def test_context_warnings_footer_does_not_trigger_a_heart():
    message = (
        "check this\n\n--- Context Warnings ---\n- Thanks for choosing Google Cloud"
    )

    assert _reactions(message) == []


def test_both_footers_do_not_trigger_a_heart():
    message = (
        "neutral\n\n--- Context Warnings ---\n- Thanks!\n\n"
        "--- Attached Context ---\n\nMade with \u2764\ufe0f"
    )

    assert _reactions(message) == []


def test_typed_affection_still_triggers_a_heart():
    assert _reactions("thanks!") == ["vibe"]


def test_typed_affection_before_footer_still_triggers_a_heart():
    message = "thanks!\n\n--- Attached Context ---\n\nneutral content"

    assert _reactions(message) == ["vibe"]


def test_non_string_content_is_a_noop():
    assert _reactions(["thanks"]) == []
