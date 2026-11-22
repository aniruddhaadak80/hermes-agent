"""Regression tests for #158050: a write_file call whose content is already on disk
must tell the model not to re-send it, regardless of file size.
"""

from types import SimpleNamespace
from unittest.mock import patch

import tools.file_tools as ft


def _hint(new_content: str, old_content: str | None, error: str | None = None):
    ops = SimpleNamespace(
        read_file_raw=lambda _path: SimpleNamespace(content=old_content, error=error)
    )
    with patch.object(ft, "_get_file_ops", return_value=ops):
        return ft._whole_file_rewrite_hint("task", "/work/file.txt", new_content)


def test_identical_small_file_gets_a_no_rewrite_hint():
    hint = _hint("hello\nworld\n", "hello\nworld\n")

    assert hint is not None
    assert "Nothing changed" in hint
    assert "do not write it again" in hint.lower()
    assert "patch" in hint.lower()


def test_identical_single_line_gets_a_no_rewrite_hint():
    hint = _hint("ok", "ok")

    assert hint is not None and "Nothing changed" in hint


def test_different_small_file_has_no_hint():
    assert _hint("hello\nworld\n", "hello\nthere\n") is None


def test_read_failure_has_no_hint():
    assert _hint("hello\nworld\n", None, error="not found") is None


def test_oversized_identical_file_is_skipped():
    content = "x" * (ft._REWRITE_HINT_MAX_CHARS + 1)

    assert _hint(content, content) is None


def test_existing_large_mostly_unchanged_hint_is_preserved():
    old = "\n".join(f"line {i}" for i in range(4000)) + "\n"
    assert len(old) >= ft._REWRITE_HINT_MIN_CHARS
    new = old.replace("line 0", "changed 0", 1)

    hint = _hint(new, old)

    assert hint is not None
    assert "lines were already on disk" in hint
    assert "patch" in hint.lower()
