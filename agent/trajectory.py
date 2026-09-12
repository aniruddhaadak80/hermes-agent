"""Trajectory saving + scratchpad helpers (``_convert_to_trajectory_format`` stays an AIAgent method — batch_runner.py calls it)."""

import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Bounded wait for the advisory lock before a save is skipped (fail-closed).
TRAJECTORY_LOCK_TIMEOUT_SECONDS = 10.0


def convert_scratchpad_to_think(content: str) -> str:
    """Convert <REASONING_SCRATCHPAD> tags to <think> tags."""
    if not content or "<REASONING_SCRATCHPAD>" not in content:
        return content
    return content.replace("<REASONING_SCRATCHPAD>", "<think>").replace("</REASONING_SCRATCHPAD>", "</think>")


def has_incomplete_scratchpad(content: str) -> bool:
    """Whether content has an opening <REASONING_SCRATCHPAD> without a closing tag."""
    return bool(content) and "<REASONING_SCRATCHPAD>" in content and "</REASONING_SCRATCHPAD>" not in content


def _lock_append_handle(f, acquire: bool, timeout: float | None = None) -> None:
    """Exclusive whole-file lock on an append handle: ``flock`` on POSIX, a 1-byte
    ``msvcrt.locking`` range at offset 0 on Windows (append position is restored by the OS).

    With ``timeout`` set, acquisition retries non-blocking until the deadline and
    raises ``TimeoutError`` instead of blocking forever, so a stalled holder costs
    one dropped sample instead of a hung batch worker.
    """
    if not acquire:
        if os.name == "nt":
            import msvcrt
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            f.seek(0, os.SEEK_END)
        else:
            import fcntl
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        return
    if timeout is None:
        if os.name == "nt":
            import msvcrt
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
            f.seek(0, os.SEEK_END)
        else:
            import fcntl
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        return
    deadline = time.monotonic() + timeout
    while True:
        try:
            if os.name == "nt":
                import msvcrt
                f.seek(0)
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                f.seek(0, os.SEEK_END)
            else:
                import fcntl
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return
        except OSError:
            if time.monotonic() >= deadline:
                raise TimeoutError(f"trajectory lock not acquired within {timeout}s: {f.name}")
            time.sleep(0.05)


def save_trajectory(trajectory: List[Dict[str, Any]], model: str, completed: bool, filename: str = None):
    """Append a ShareGPT-format entry to a JSONL file (default trajectory_samples.jsonl / failed_trajectories.jsonl by ``completed``).

    Appends are serialized across processes with an advisory lock on the file
    handle (whole-file ``flock`` on POSIX, 1-byte ``msvcrt.locking`` range on
    Windows); if the lock cannot be acquired within
    :data:`TRAJECTORY_LOCK_TIMEOUT_SECONDS` the save is skipped (logged)
    rather than stalling the writer or landing unserialized (#12684).
    """
    if filename is None:
        filename = "trajectory_samples.jsonl" if completed else "failed_trajectories.jsonl"
    entry = {"conversations": trajectory, "timestamp": datetime.now().isoformat(), "model": model, "completed": completed}
    try:
        line = json.dumps(entry, ensure_ascii=False) + "\n"  # serialize before taking the lock
        with open(filename, "a", encoding="utf-8") as f:
            # Gateway sessions and batch workers append to the SAME default file; without an
            # exclusive lock around write+flush, entries larger than one write() interleave and the
            # JSONL stops parsing (#12684).
            _lock_append_handle(f, True, timeout=TRAJECTORY_LOCK_TIMEOUT_SECONDS)
            try:
                f.write(line)
                f.flush()
            finally:
                _lock_append_handle(f, False)
        logger.info("Trajectory saved to %s", filename)
    except TimeoutError as e:
        logger.warning("Trajectory not saved (lock contention): %s", e)
    except Exception as e:
        logger.warning("Failed to save trajectory: %s", e)
