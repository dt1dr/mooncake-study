"""Calculate standard MHA/GQA payloads from local model configurations."""

import json
from pathlib import Path

from common.artifacts import write_summary


def kv_bytes(
    config: dict[str, int], tokens: int, bytes_per_element: int, batch_size: int = 1
) -> int:
    layers = config["num_hidden_layers"]
    kv_heads = config["num_key_value_heads"]
    head_dim = config["head_dim"]
    return 2 * layers * kv_heads * head_dim * tokens * bytes_per_element * batch_size


def main(directory: Path) -> int:
    reference = json.loads((directory / "expected/calculator.json").read_text(encoding="utf-8"))
    metrics = {}
    print(f"{'Case':32} {'Bytes':>14} {'GB':>12} {'GiB':>10}")
    for case in reference["cases"]:
        config = reference["models"][case["model"]] | case["overrides"]
        size = kv_bytes(config, case["tokens"], case["bytes_per_element"], case["batch_size"])
        metrics[case["id"]] = {"bytes": size, "GB": size / 10**9, "GiB": size / 2**30}
        print(f"{case['id']:32} {size:14d} {size / 10**9:12.5f} {size / 2**30:10.5f}")
    return write_summary(directory, metrics, {"kv-footprint": list(metrics)})
