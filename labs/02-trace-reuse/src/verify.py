"""Compare recorded tokens with hand-derived and external references, without replay."""

import json
from pathlib import Path
from typing import Any


def main(directory: Path, summary: dict[str, Any]) -> int:
    cases = json.loads((directory / "expected/hand-traces.json").read_text(encoding="utf-8"))
    expected = {
        case["id"]: {
            "hit_tokens": case["hit_tokens"],
            "nc1_hit_tokens": [0] * len(case["requests"]),
        }
        for case in cases
    }
    reference = json.loads((directory / "expected/official-curve.json").read_text(encoding="utf-8"))
    curve = reference["expected"]
    expected["official-curve"] = curve | {
        "points": [point | {"nc1_hit_tokens": 0} for point in curve["points"]]
    }
    if summary["metrics"] != expected:
        print("failed: lab02 hits, measurement window or NC1 differ from the references")
        return 1
    if [claim["id"] for claim in summary["claims"]] != ["prefix-mechanism", "official-curve"]:
        print("failed: lab02 requires both prefix-mechanism and official-curve evidence")
        return 1
    print(
        f"passed: lab02, {len(cases)} hand traces, {len(curve['points'])} official points and NC1"
    )
    return 0
