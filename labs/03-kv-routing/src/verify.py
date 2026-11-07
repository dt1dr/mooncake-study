"""Check NC1 equivalence and the registered routing-trend hypothesis on saved results."""

from pathlib import Path
from statistics import mean
from typing import Any

from common.routing import BASELINE, POLICIES, REQUESTS, SCENARIOS, SEEDS


def totals(metrics: dict[str, Any], scenario: str, policy: str) -> list[float]:
    return [run["ttft_sum"] for run in metrics[scenario]["baseline"][policy]]


def gap(metrics: dict[str, Any], scenario: str) -> float:
    """Seed-averaged total TTFT saved by cache-aware routing over least-loaded."""
    least = totals(metrics, scenario, "least-loaded")
    aware = totals(metrics, scenario, "cache-aware")
    return mean(a - b for a, b in zip(least, aware, strict=True))


def main(directory: Path, summary: dict[str, Any]) -> int:
    metrics = summary["metrics"]
    if list(metrics) != list(SCENARIOS) or any(
        metrics[name]["settings"] != BASELINE | change
        or metrics[name]["seeds"] != list(SEEDS)
        or any(
            set(metrics[name][group]) != set(POLICIES)
            or any(len(runs) != len(SEEDS) for runs in metrics[name][group].values())
            for group in ("baseline", "nc1")
        )
        or any(
            len(run["workers"]) != REQUESTS
            for runs in metrics[name]["nc1"].values()
            for run in runs
        )
        for name, change in SCENARIOS.items()
    ):
        print("failed: results do not cover the registered sweep")
        return 1

    def lower(name: str) -> bool:
        least, aware = totals(metrics, name, "least-loaded"), totals(metrics, name, "cache-aware")
        return all(a < b for a, b in zip(aware, least, strict=True))

    def equal(name: str) -> bool:
        return totals(metrics, name, "least-loaded") == totals(metrics, name, "cache-aware")

    g = {name: gap(metrics, name) for name in SCENARIOS}
    checks = {
        "NC1: cache-aware decisions and TTFT statistics equal least-loaded": all(
            metrics[name]["nc1"]["cache-aware"] == metrics[name]["nc1"]["least-loaded"]
            for name in SCENARIOS
        ),
        "NC1: zero hit tokens for every policy": all(
            run["hit_tokens"] == 0
            for name in SCENARIOS
            for runs in metrics[name]["nc1"].values()
            for run in runs
        ),
        "(a) cache-aware lower in every seed at spacing 24/32/48": all(
            lower(name) for name in ("spacing-24", "baseline", "spacing-48")
        ),
        "(b) exactly equal without reuse benefit": all(
            equal(name) for name in ("unique-prefixes", "capacity-0", "read-cost-4")
        ),
        "(c) gap peaks at 4 prefixes": all(
            g["baseline"] > g[name] for name in ("prefixes-2", "prefixes-8", "prefixes-16")
        ),
        "(c) gap peaks at capacity 8": all(
            g["baseline"] > g[name] for name in ("capacity-4", "capacity-16")
        ),
        "(c) gap shrinks as read cost rises": g["baseline"] > g["read-cost-2"] > g["read-cost-4"],
    }
    for name, passed in checks.items():
        print(f"{'ok  ' if passed else 'FAIL'} {name}")
    if not all(checks.values()):
        print("failed: lab03")
        return 1
    print(f"passed: lab03, {len(SCENARIOS)} scenarios x {len(SEEDS)} seeds")
    return 0
