"""Regression tests for #158043: a background-process completion notification must
keep a non-empty output tail, even when the bounded window ends at a newline.
"""

from types import SimpleNamespace

from gateway.run_notifications import GatewayNotificationsMixin


def _completion_output(raw: str) -> str:
    session = SimpleNamespace(
        output_buffer=raw,
        command="",
        exit_code=0,
        started_at=None,
        task_id="",
        owner_task_id="",
        completion_reason="exited",
        termination_source="",
    )
    return GatewayNotificationsMixin._build_process_completion_event(
        {}, session, "proc_1"
    )["output"]


def test_single_long_line_ending_in_newline_keeps_its_tail():
    raw = '{"result": ' + "x" * 3000 + "}\n"

    output = _completion_output(raw)
    marker, _, tail = output.partition("\n")

    assert "truncated" in marker
    assert tail == raw[-2000:]
    assert "x" in tail


def test_multiline_output_still_starts_at_a_line_boundary():
    raw = "".join(f"line {i:03d} " + ("y" * 90) + "\n" for i in range(40))
    assert len(raw) > 2000

    output = _completion_output(raw)
    marker, _, tail = output.partition("\n")

    assert "truncated" in marker
    start = raw.index(tail)
    assert start > 0
    assert raw[start - 1] == "\n"
    assert tail.endswith("\n")


def test_short_output_is_not_marked_truncated():
    raw = "all good\n"

    assert _completion_output(raw) == raw
