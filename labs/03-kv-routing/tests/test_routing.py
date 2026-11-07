import runpy
import shutil
from copy import deepcopy
from pathlib import Path

import pytest

from common.cli import invoke, run_lab, verify_lab
from common.prefix_cache import LeafLRU
from common.routing import BASELINE, SCENARIOS, simulate


def test_match_does_not_change_recency():
    cache = LeafLRU(2)
    cache.access([1])
    cache.access([2])
    assert cache.match([1]) == 1
    cache.access([3])
    assert cache.match([1]) == 0


def test_completion_visibility_and_queue():
    requests = [{"timestamp": t, "input_length": 4, "hash_ids": [1]} for t in (0, 1, 32)]
    assert simulate(requests, "least-loaded", capacity=1, workers=1) == [
        {"worker": 0, "hit_tokens": 0, "ttft": 16},
        {"worker": 0, "hit_tokens": 0, "ttft": 31},
        {"worker": 0, "hit_tokens": 4, "ttft": 4},
    ]


def test_cache_aware_selects_reusable_worker():
    requests = [
        {"timestamp": 0, "input_length": 4, "hash_ids": [1]},
        {"timestamp": 1, "input_length": 4, "hash_ids": [2]},
        {"timestamp": 20, "input_length": 4, "hash_ids": [2]},
    ]
    aware = simulate(requests, "cache-aware", capacity=1)
    least = simulate(requests, "least-loaded", capacity=1)
    assert aware[-1] == {"worker": 1, "hit_tokens": 4, "ttft": 4}
    assert least[-1] == {"worker": 0, "hit_tokens": 0, "ttft": 16}


def test_idle_ties_go_to_least_recently_assigned_worker():
    requests = [{"timestamp": t, "input_length": 4, "hash_ids": [1]} for t in (0, 100, 200)]
    least = simulate(requests, "least-loaded", capacity=1)
    aware = simulate(requests, "cache-aware", capacity=1)
    assert [r["worker"] for r in least] == [0, 1, 0]
    assert [r["hit_tokens"] for r in least] == [0, 0, 4]
    assert [r["worker"] for r in aware] == [0, 0, 0]
    assert [r["hit_tokens"] for r in aware] == [0, 4, 4]


def test_run_then_verify(tmp_path):
    lab = Path(__file__).resolve().parents[1]
    directory = tmp_path / lab.name
    shutil.copytree(lab, directory, ignore=shutil.ignore_patterns("results", "__pycache__"))
    assert run_lab(directory) == 0
    assert verify_lab(directory) == 0


@pytest.fixture(scope="module")
def sweep():
    lab = Path(__file__).resolve().parents[1]
    run_scenario = runpy.run_path(str(lab / "src/run.py"))["run_scenario"]
    return {
        "metrics": {name: run_scenario(BASELINE | change) for name, change in SCENARIOS.items()}
    }


@pytest.mark.parametrize(
    "fault", ["empty-nc1", "missing-policy", "missing-seed", "short-decisions", "wrong-worker"]
)
def test_verifier_rejects_incomplete_or_divergent_evidence(sweep, fault):
    broken = deepcopy(sweep)
    scenario = broken["metrics"]["baseline"]
    control = scenario["nc1"]
    if fault == "empty-nc1":
        for policy in control:
            control[policy] = []
    elif fault == "missing-policy":
        del control["random"]
    elif fault == "missing-seed":
        for runs in scenario["baseline"].values():
            runs.pop()
    elif fault == "short-decisions":
        for runs in control.values():
            runs[0]["workers"].pop()
    else:
        workers = control["cache-aware"][0]["workers"]
        workers[0] = 1 - workers[0]
    lab = Path(__file__).resolve().parents[1]
    assert invoke(lab, "verify", broken) == 1
