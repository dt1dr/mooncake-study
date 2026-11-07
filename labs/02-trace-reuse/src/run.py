"""Run hand traces and the official-trace capacity sweep, with NC1 controls."""

import json
from pathlib import Path
from typing import Any

from common.artifacts import write_summary
from common.prefix_cache import replay
from common.trace import Request, load_trace, nc1


def sweep(requests: list[Request], settings: dict[str, Any]) -> dict[str, Any]:
    warmup = int(len(requests) * settings["warmup_fraction"])
    total = sum(request["input_length"] for request in requests[warmup:])
    control = nc1(requests)
    points = []
    for gib in settings["budgets_gib"]:
        capacity = gib * 2**30 // (settings["bytes_per_token"] * settings["block_size"])
        measured = replay(requests, capacity, settings["block_size"], warmup)
        if measured is None:
            print(f"{gib} GiB: underfilled during warmup; omit this and larger budgets")
            break
        hits = sum(measured)
        control_hits = sum(replay(control, capacity, settings["block_size"], warmup))
        points.append({"gib": gib, "hit_tokens": hits, "nc1_hit_tokens": control_hits})
        print(f"{gib:5} GiB: {hits}/{total} hit tokens ({hits / total:.2%}); NC1 {control_hits}")
    return {
        "request_count": len(requests),
        "warmup_requests": warmup,
        "total_tokens": total,
        "points": points,
    }


def plot_curve(directory: Path, curve: dict[str, Any], reference: dict[str, Any]) -> None:
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    figure = Figure(figsize=(7, 4), layout="constrained")
    FigureCanvasAgg(figure)
    axis = figure.subplots()
    points = curve["points"]
    budgets = [point["gib"] for point in points]
    axis.plot(budgets, [p["hit_tokens"] / curve["total_tokens"] for p in points], label="Replay")
    expected = reference["expected"]
    axis.scatter(
        [p["gib"] for p in expected["points"]],
        [p["hit_tokens"] / expected["total_tokens"] for p in expected["points"]],
        marker="x",
        label="Official Python reference",
    )
    axis.plot(
        budgets,
        [p["nc1_hit_tokens"] / curve["total_tokens"] for p in points],
        linestyle="--",
        label="NC1",
    )
    axis.set(
        xscale="log", xlabel="KV budget (GiB)", ylabel="Token-weighted hit rate", ylim=(-0.02, 1)
    )
    axis.set_title(f"{reference['trace']} · {reference['model']} · {reference['precision']} · LRU")
    axis.legend()
    (directory / "results").mkdir(exist_ok=True)
    figure.savefig(directory / "results/curve.png", dpi=160)


def main(directory: Path) -> int:
    reference = json.loads((directory / "expected/official-curve.json").read_text(encoding="utf-8"))
    try:
        requests = load_trace(reference["trace"])
    except FileNotFoundError as exc:
        print(f"not tested: {exc}")
        return 3
    cases = json.loads((directory / "expected/hand-traces.json").read_text(encoding="utf-8"))
    metrics: dict[str, Any] = {}
    for case in cases:
        hand_requests = case["requests"]
        capacity, block_size = case["capacity_blocks"], case["block_size"]
        baseline = replay(hand_requests, capacity, block_size)
        control = replay(nc1(hand_requests), capacity, block_size)
        metrics[case["id"]] = {"hit_tokens": baseline, "nc1_hit_tokens": control}
        print(f"{case['id']}: hit tokens {baseline}; NC1 {control}")
    metrics["official-curve"] = sweep(requests, reference)
    plot_curve(directory, metrics["official-curve"], reference)
    hand_ids = [case["id"] for case in cases]
    claims = {"prefix-mechanism": hand_ids, "official-curve": ["official-curve"]}
    return write_summary(directory, metrics, claims)
