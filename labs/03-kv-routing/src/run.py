"""Run the registered one-factor routing sweep with NC1 controls."""

from pathlib import Path
from statistics import mean, quantiles
from typing import Any

from common.artifacts import write_summary
from common.routing import (
    BASELINE,
    POLICIES,
    REQUESTS,
    SCENARIOS,
    SEEDS,
    RouteResult,
    simulate,
    workload,
)
from common.trace import Request, nc1

SLO = 64  # TTFT target in time units: one uncached 16-token prefill.


def summarize(requests: list[Request], rows: list[RouteResult]) -> dict[str, float]:
    ttft = [row["ttft"] for row in rows]
    return {
        "ttft_sum": sum(ttft),
        "p50": quantiles(ttft, n=100, method="inclusive")[49],
        "p95": quantiles(ttft, n=100, method="inclusive")[94],
        "slo_met": sum(t <= SLO for t in ttft),
        "makespan": max(r["timestamp"] + t for r, t in zip(requests, ttft, strict=True)),
        "hit_tokens": sum(row["hit_tokens"] for row in rows),
    }


def run_scenario(settings: dict[str, int]) -> dict[str, Any]:
    baseline: dict[str, list[dict[str, float]]] = {policy: [] for policy in POLICIES}
    control: dict[str, list[dict[str, Any]]] = {policy: [] for policy in POLICIES}
    for seed in SEEDS:
        requests = workload(seed, settings["prefixes"], settings["spacing"])
        options = {"capacity": settings["capacity"], "read_cost": settings["read_cost"]}
        for policy in POLICIES:
            rows = simulate(requests, policy, seed=seed, **options)
            baseline[policy].append(summarize(requests, rows))
            rows = simulate(nc1(requests), policy, seed=seed, **options)
            workers = [row["worker"] for row in rows]
            control[policy].append(summarize(requests, rows) | {"workers": workers})
    return {"settings": settings, "seeds": list(SEEDS), "baseline": baseline, "nc1": control}


def plot_sensitivity(directory: Path, metrics: dict[str, Any]) -> None:
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    figure = Figure(figsize=(12, 3.5), layout="constrained")
    FigureCanvasAgg(figure)
    for axis, (factor, label) in zip(
        figure.subplots(1, 3),
        (
            ("prefixes", "Shared prefixes"),
            ("capacity", "Cache blocks / worker"),
            ("read_cost", "Read cost / token"),
        ),
        strict=True,
    ):
        scenarios = sorted(
            (
                scenario
                for scenario in metrics.values()
                if all(
                    scenario["settings"][key] == value
                    for key, value in BASELINE.items()
                    if key != factor
                )
                and scenario["settings"][factor] > 0
            ),
            key=lambda scenario: scenario["settings"][factor],
        )
        gaps = [
            [
                (least["ttft_sum"] - aware["ttft_sum"]) / REQUESTS
                for least, aware in zip(
                    scenario["baseline"]["least-loaded"],
                    scenario["baseline"]["cache-aware"],
                    strict=True,
                )
            ]
            for scenario in scenarios
        ]
        x = [scenario["settings"][factor] for scenario in scenarios]
        axis.plot(x, [mean(values) for values in gaps], "o-", label="Seed mean")
        axis.fill_between(
            x,
            [min(values) for values in gaps],
            [max(values) for values in gaps],
            alpha=0.2,
            label="Seed min–max",
        )
        axis.axhline(0, color="gray", linewidth=0.8)
        axis.set(xlabel=label, xticks=x)
    figure.axes[0].set_ylabel("Mean TTFT saved (time units)\nleast-loaded − cache-aware")
    figure.axes[-1].legend()
    figure.suptitle(f"One-factor sweep · seeds {SEEDS[0]}–{SEEDS[-1]}")
    figure.savefig(directory / "results/sensitivity.png", dpi=160)


def main(directory: Path) -> int:
    metrics = {}
    print(f"Mean TTFT over seeds {SEEDS[0]}-{SEEDS[-1]} (min..max of per-seed means)")
    for name, change in SCENARIOS.items():
        metrics[name] = run_scenario(BASELINE | change)
        line = f"{name:16}"
        for policy, runs in metrics[name]["baseline"].items():
            means = [run["ttft_sum"] / REQUESTS for run in runs]
            line += f"  {policy} {mean(means):6.1f} ({min(means):.0f}..{max(means):.0f})"
        print(line)
    scenarios = list(metrics)
    claims = {"routing-mechanism": scenarios, "routing-trend": scenarios}
    code = write_summary(directory, metrics, claims)
    plot_sensitivity(directory, metrics)
    return code
