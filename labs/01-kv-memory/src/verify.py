"""Compare stored measurements against independently captured calculator outputs."""

import json
from pathlib import Path
from typing import Any


def main(directory: Path, summary: dict[str, Any]) -> int:
    reference = json.loads((directory / "expected/calculator.json").read_text(encoding="utf-8"))
    expected = {
        case["id"]: {
            "bytes": case["total_bytes"],
            "GB": case["total_bytes"] / 10**9,
            "GiB": case["total_bytes"] / 2**30,
        }
        for case in reference["cases"]
    }
    if summary["metrics"] != expected:
        print("failed: lab01 measurements differ from the pinned calculator reference")
        return 1
    print(f"passed: lab01, {len(expected)} cases match the official calculator exactly")
    return 0
