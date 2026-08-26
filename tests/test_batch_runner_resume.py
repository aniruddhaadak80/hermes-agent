"""Regression tests for batch_runner --resume correctness (#95322).

Covers: non-string prompt rows no longer crash the resume filter, and
resumed runs continue shard numbering after existing shards instead of
appending into the previous run's batch files.
"""

import json
from pathlib import Path

from batch_runner import BatchRunner, _entry_prompt_text


def _make_runner(tmp_path, dataset):
    """Build a BatchRunner without the file/agent heavy __init__."""
    runner = BatchRunner.__new__(BatchRunner)
    runner.dataset = dataset
    runner.batches = []
    runner.output_dir = tmp_path / "out"
    runner.checkpoint_file = runner.output_dir / "checkpoint.json"
    runner.run_name = "resume-test"
    runner.batch_size = 2
    runner.num_workers = 1
    runner.api_key = None
    runner.base_url = None
    runner.model = "test-model"
    runner.distribution = "default"
    runner.max_iterations = 1
    runner.verbose = False
    runner.ephemeral_system_prompt = None
    runner.log_prefix_chars = 20
    runner.providers_allowed = None
    runner.providers_ignored = None
    runner.providers_order = None
    runner.provider_sort = None
    runner.openrouter_min_coding_score = None
    runner.max_tokens = None
    runner.reasoning_config = None
    runner.prefill_messages = None
    runner.max_samples = None
    runner.stats_file = runner.output_dir / "stats.json"
    return runner


def test_filter_dataset_tolerates_non_string_prompt(tmp_path):
    """A malformed row (prompt: 123) must not crash the resume filter."""
    runner = _make_runner(
        tmp_path,
        [{"prompt": 123}, {"prompt": "real prompt"}],
    )

    filtered, skipped = runner._filter_dataset_by_completed({"real prompt"})

    # str(123) == "123" is a distinct text; only the real prompt was done.
    assert [idx for idx, _ in filtered] == [0]
    assert skipped == [1]


def test_entry_prompt_text_non_string_returns_text():
    assert _entry_prompt_text({"prompt": 123}) == "123"
    assert _entry_prompt_text({"prompt": None}) == ""
    assert _entry_prompt_text("not-a-dict") == ""


def test_existing_max_shard_number_from_stats_and_files(tmp_path):
    runner = _make_runner(tmp_path, [{"prompt": "a"}])
    runner.output_dir.mkdir(parents=True)
    (runner.output_dir / "batch_0.jsonl").write_text("{}\n", encoding="utf-8")
    (runner.output_dir / "batch_7.jsonl").write_text("{}\n", encoding="utf-8")

    checkpoint = {"batch_stats": {"7": {"processed": 1}}}

    assert runner._existing_max_shard_number(checkpoint) == 7


def test_existing_max_shard_number_empty_state(tmp_path):
    runner = _make_runner(tmp_path, [{"prompt": "a"}])
    assert runner._existing_max_shard_number({}) == -1


def test_resume_shard_numbering_continues_past_existing(tmp_path, monkeypatch):
    """Resume must number new shards after existing ones — appending into
    the previous run's batch_N.jsonl corrupted stats (#95322)."""
    runner = _make_runner(
        tmp_path,
        [{"prompt": "done"}, {"prompt": "pending"}],
    )
    runner.output_dir.mkdir(parents=True)
    (runner.output_dir / "batch_3.jsonl").write_text(
        json.dumps({"conversations": [], "prompt_text": "done"}) + "\n",
        encoding="utf-8",
    )

    captured = {}

    class _FakePool:
        def __init__(self, processes):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def imap_unordered(self, fn, tasks):
            captured["shard_numbers"] = [t[0] for t in tasks]
            return iter([])

    import batch_runner as br

    monkeypatch.setattr(br, "Pool", _FakePool)
    monkeypatch.setattr(
        runner, "_scan_completed_prompts_by_content", lambda: {"done"}
    )

    runner.run(resume=True)

    # One remaining prompt, one new batch — numbered AFTER existing shard 3.
    assert captured["shard_numbers"] == [4]
