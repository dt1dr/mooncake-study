import json
import runpy
import shutil
from pathlib import Path

from common.cli import run_lab, verify_lab

LAB = Path(__file__).resolve().parents[1]
kv_bytes = runpy.run_path(str(LAB / "src/run.py"))["kv_bytes"]
REFERENCE = json.loads((LAB / "expected/calculator.json").read_text(encoding="utf-8"))


def test_tiny_mha_counts_keys_and_values():
    config = {"num_hidden_layers": 2, "num_key_value_heads": 3, "head_dim": 5}
    # 2 layers * (3 * 5 keys + 3 * 5 values) * 7 tokens * 2 bytes * 2 sequences.
    assert kv_bytes(config, 7, 2, 2) == 1680


def test_run_then_verify_without_git(tmp_path, monkeypatch):
    from env import check_env

    command = check_env.command
    monkeypatch.setattr(
        check_env,
        "command",
        lambda args: {"returncode": 1, "output": ""} if args[0] == "git" else command(args),
    )
    directory = tmp_path / LAB.name
    shutil.copytree(LAB, directory, ignore=shutil.ignore_patterns("results", "__pycache__"))
    assert run_lab(directory) == 0
    assert verify_lab(directory) == 0

    path = directory / "results/summary.json"
    summary = json.loads(path.read_text())
    assert summary["env_report"]["git_sha"] is None
    summary["metrics"][REFERENCE["cases"][0]["id"]]["bytes"] += 1
    path.write_text(json.dumps(summary))
    before = path.read_bytes()
    assert verify_lab(directory) == 1
    assert path.read_bytes() == before
