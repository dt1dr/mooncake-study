"""Read result envelopes. Claim levels live in lab.yaml; summaries carry the evidence."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from common.metadata import load_lab, validate
from env import check_env

NOT_TESTED = 3


def write_summary(directory: Path, metrics: dict[str, Any], claims: dict[str, list[str]]) -> int:
    """Save metrics; `claims` maps each claim ID to the metric keys that support it."""
    report = check_env.collect_report()
    summary = {
        "lab_id": load_lab(directory)["id"],
        "created_at": datetime.now(UTC).isoformat(),
        "env_report": report,
        "claims": [{"id": claim, "evidence": keys} for claim, keys in claims.items()],
        "metrics": metrics,
    }
    validate(summary, "summary")
    output = directory / "results/summary.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return 0


def read_summary(directory: Path) -> dict[str, Any] | None:
    path = directory / "results" / "summary.json"
    if not path.exists():
        return None
    summary = json.loads(path.read_text(encoding="utf-8"))
    validate(summary, "summary")
    metadata = load_lab(directory)
    if summary["lab_id"] != metadata["id"]:
        raise ValueError("Result belongs to a different lab")
    registered = {claim["id"] for claim in metadata["claims"]}
    result_ids = [claim["id"] for claim in summary["claims"]]
    if len(result_ids) != len(set(result_ids)) or not set(result_ids) <= registered:
        raise ValueError("Result has duplicate or unregistered claims")
    for claim in summary["claims"]:
        if not set(claim["evidence"]) <= summary["metrics"].keys():
            raise ValueError(f"Evidence for {claim['id']} names missing metrics")
    return summary
