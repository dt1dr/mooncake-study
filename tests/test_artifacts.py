import json
import shutil

import pytest

from common.cli import run_lab, verify_lab
from common.metadata import lab_directory


@pytest.fixture
def lab(tmp_path):
    directory = tmp_path / "01-kv-memory"
    shutil.copytree(lab_directory("01"), directory, ignore=shutil.ignore_patterns("results"))
    return directory


def write_summary(lab, **changes):
    summary = {
        "lab_id": "01",
        "created_at": "2026-10-29T00:00:00+00:00",
        "env_report": {
            "fingerprint": "a" * 64,
            "git_sha": "c" * 40,
            "uv_lock_sha256": "b" * 64,
            "python": "3.13.17",
            "platform": "Linux",
            "packages": {},
        },
        "claims": [{"id": "kv-footprint", "evidence": ["70b-8k-bf16"]}],
        "metrics": {"70b-8k-bf16": {"bytes": 1}},
    }
    summary.update(changes)
    (lab / "results").mkdir(exist_ok=True)
    (lab / "results/summary.json").write_text(json.dumps(summary))


def test_missing_result_does_not_pass_or_write(lab):
    assert verify_lab(lab) == 3
    assert not (lab / "results").exists()


def test_wrong_lab_result_is_rejected(lab):
    write_summary(lab, lab_id="02")
    with pytest.raises(ValueError, match="different lab"):
        verify_lab(lab)


def test_unregistered_claim_is_rejected(lab):
    write_summary(lab, claims=[{"id": "made-up", "evidence": ["x"]}])
    with pytest.raises(ValueError, match="unregistered"):
        verify_lab(lab)


def test_evidence_must_name_saved_metrics(lab):
    write_summary(lab, metrics={})
    with pytest.raises(ValueError, match="missing metrics"):
        verify_lab(lab)


@pytest.mark.parametrize("outcome", [1, 3, "exception"])
def test_incomplete_rerun_invalidates_summary(lab, monkeypatch, outcome):
    write_summary(lab)

    def incomplete_run(directory, name):
        assert not (directory / "results/summary.json").exists()
        write_summary(directory)  # A runner may fail after writing, e.g. during plotting.
        if outcome == "exception":
            raise RuntimeError("interrupted run")
        return outcome

    monkeypatch.setattr("common.cli.invoke", incomplete_run)
    if outcome == "exception":
        with pytest.raises(RuntimeError, match="interrupted run"):
            run_lab(lab)
    else:
        assert run_lab(lab) == outcome
    assert verify_lab(lab) == 3
