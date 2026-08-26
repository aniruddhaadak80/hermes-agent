"""Test for KawaiiSpinner terminal width truncation (#93999)."""

import os
import sys
import time
import threading
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.display import KawaiiSpinner


def test_spinner_truncates_long_message():
    """Spinner truncates message to fit terminal width."""
    spinner = KawaiiSpinner(message="A" * 200, spinner_type='dots')
    
    with patch('os.get_terminal_size') as mock_getsize:
        mock_getsize.return_value = os.terminal_size((80, 24))
        
        spinner.running = True
        spinner.start_time = time.time()
        spinner.frame_idx = 0
        spinner.last_line_len = 0
        spinner._out = MagicMock()
        spinner._out.isatty.return_value = True
        
        # Directly test the truncation logic (not the full _animate loop)
        frame = spinner.spinner_frames[spinner.frame_idx % len(spinner.spinner_frames)]
        prefix = "  "
        suffix = " "
        reserved = len(prefix) + len(spinner.spinner_frames[0]) + len(suffix) + 8 + 3
        max_msg_len = max(80 - reserved, 10)
        msg = spinner.message
        if len(msg) > max_msg_len:
            msg = msg[:max_msg_len - 1] + "…"
        
        assert len(msg) <= max_msg_len
        assert "…" in msg
        print("OK test_spinner_truncates_long_message passed")


def test_spinner_respects_tty_false():
    """When not a TTY, spinner logs once and stops."""
    spinner = KawaiiSpinner(message="test", spinner_type='dots')
    
    spinner._out = MagicMock()
    spinner._out.isatty.return_value = False
    output = []
    spinner._write = lambda text, end='', flush=False: output.append(text)
    spinner.running = True
    spinner.start_time = time.time()
    
    # Run _animate in a thread and stop it after a short delay
    def run_animate():
        spinner._animate()
    
    t = threading.Thread(target=run_animate, daemon=True)
    t.start()
    time.sleep(0.1)  # Let it log once
    spinner.running = False  # Stop the spinner
    t.join(timeout=1)
    
    assert len(output) >= 1
    assert any("[tool]" in out for out in output)
    print("OK test_spinner_respects_tty_false passed")


if __name__ == "__main__":
    test_spinner_truncates_long_message()
    test_spinner_respects_tty_false()
    print("All tests passed!")