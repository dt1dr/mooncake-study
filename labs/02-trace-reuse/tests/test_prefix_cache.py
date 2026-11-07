import json
import shutil
from pathlib import Path

import pytest

from common.cli import run_lab, verify_lab
from common.prefix_cache import replay
from common.trace import nc1

LAB = Path(__file__).resolve().parents[1]
CASES = json.loads((LAB / "expected/hand-traces.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_hand_trace(case):
    requests = case["requests"]
    assert replay(requests, case["capacity_blocks"], case["block_size"]) == case["hit_tokens"]


def test_nc1_changes_only_cross_request_identity():
    requests = [
        {"timestamp": 8, "input_length": 12, "output_length": 3, "hash_ids": [1, 2, 1]},
        {"timestamp": 20, "input_length": 8, "output_length": 5, "hash_ids": [1, 2]},
    ]
    control = nc1(requests)
    for original, changed in zip(requests, control, strict=True):
        assert changed | {"hash_ids": None} == original | {"hash_ids": None}
    assert control[0]["hash_ids"][0] == control[0]["hash_ids"][2]
    assert set(control[0]["hash_ids"]).isdisjoint(control[1]["hash_ids"])


def test_measured_window():
    requests = [
        {"input_length": 6, "hash_ids": [1, 2]},
        {"input_length": 8, "hash_ids": [1, 2]},
        {"input_length": 5, "hash_ids": [1, 2]},
    ]
    assert replay(requests, 2, 4, warmup=1) == [8, 5]
    assert replay(requests, 2, 4, warmup=2) == [5]


def test_budget_must_fill_during_warmup():
    requests = [
        {"input_length": 4, "hash_ids": [1]},
        {"input_length": 8, "hash_ids": [1, 2]},
        {"input_length": 8, "hash_ids": [1, 2]},
    ]
    assert replay(requests, 2, 4, warmup=1) is None
    assert replay(requests, 2, 4, warmup=2) == [8]
    # Having been full once is enough, even if the request then evicts its own tail.
    assert replay([{"input_length": 12, "hash_ids": [1, 2, 3]}] * 2, 2, 4, warmup=1) == [4]


def test_run_then_verify(tmp_path, monkeypatch):
    directory = tmp_path / LAB.name
    shutil.copytree(LAB, directory, ignore=shutil.ignore_patterns("results", "__pycache__"))
    monkeypatch.setattr(
        "common.trace.load_trace", lambda name: [{"input_length": 6, "hash_ids": [1, 2]}] * 8
    )
    # A toy curve that can be counted by hand: 1 GiB = 2 blocks; all 4 measured requests hit.
    reference = {
        "trace": "toy",
        "model": "toy",
        "precision": "bf16",
        "block_size": 4,
        "bytes_per_token": 2**27,
        "warmup_fraction": 0.5,
        "budgets_gib": [1, 2],
        "expected": {
            "request_count": 8,
            "warmup_requests": 4,
            "total_tokens": 24,
            "points": [{"gib": 1, "hit_tokens": 24}],
        },
    }
    (directory / "expected/official-curve.json").write_text(json.dumps(reference))
    assert run_lab(directory) == 0
    assert verify_lab(directory) == 0

    path = directory / "results/summary.json"
    summary = json.loads(path.read_text())
    summary["metrics"]["official-curve"]["points"][0]["nc1_hit_tokens"] = 1
    path.write_text(json.dumps(summary))
    assert verify_lab(directory) == 1
