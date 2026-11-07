"""Read a staged, checksum-pinned trace without downloading it."""

import hashlib
import json
from collections.abc import Hashable, Sequence
from typing import NotRequired, TypedDict

from common.metadata import ROOT


class Request(TypedDict):
    input_length: int
    hash_ids: list[Hashable]
    timestamp: NotRequired[float]
    output_length: NotRequired[int]


def load_trace(name: str) -> list[Request]:
    entry = json.loads((ROOT / "data/manifest.json").read_text(encoding="utf-8"))["files"][name]
    path = ROOT / "data/raw" / entry["filename"]
    if not path.exists():
        raise FileNotFoundError(f"Stage the trace first: uv run python data/fetch.py {name}")
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != entry["sha256"]:
        raise ValueError(f"Trace SHA256 mismatch: {path}")
    return [json.loads(line) for line in content.splitlines() if line.strip()]


def nc1(requests: Sequence[Request]) -> list[Request]:
    """Give each request its own block-ID namespace; keep everything else unchanged."""
    return [
        {**request, "hash_ids": [(index, block) for block in request["hash_ids"]]}
        for index, request in enumerate(requests)
    ]
