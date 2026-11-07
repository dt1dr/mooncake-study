"""Serial workers with dispatch-time KV snapshots and completion-time cache admission."""

import heapq
import random
from collections.abc import Hashable, Iterable
from typing import TypedDict

from common.prefix_cache import LeafLRU
from common.trace import Request

POLICIES = ("random", "least-loaded", "cache-aware")
REQUESTS = 120
SEEDS = tuple(range(200, 210))  # Held out: exploration used 42-44 and 100-109.
BASELINE = {"prefixes": 4, "capacity": 8, "spacing": 32, "read_cost": 1}
# One-factor changes around the baseline. prefixes=0 gives every request a unique prefix.
SCENARIOS = {
    "baseline": {},
    "prefixes-2": {"prefixes": 2},
    "prefixes-8": {"prefixes": 8},
    "prefixes-16": {"prefixes": 16},
    "unique-prefixes": {"prefixes": 0},
    "capacity-0": {"capacity": 0},
    "capacity-4": {"capacity": 4},
    "capacity-16": {"capacity": 16},
    "read-cost-2": {"read_cost": 2},
    "read-cost-4": {"read_cost": 4},
    "spacing-24": {"spacing": 24},
    "spacing-48": {"spacing": 48},
}


class RouteResult(TypedDict):
    worker: int
    hit_tokens: int
    ttft: float


def simulate(
    requests: Iterable[Request],
    policy: str,
    *,
    capacity: int,
    read_cost: float = 1,
    workers: int = 2,
    block_size: int = 4,
    seed: int = 42,
) -> list[RouteResult]:
    rng = random.Random(seed + 1_000_000)  # Separate routing and workload random streams.
    caches = [LeafLRU(capacity) for _ in range(workers)]
    available: list[float] = [0] * workers
    last_assigned = [-1] * workers
    events: list[tuple[float, int, int, list[Hashable]]] = []
    rows: list[RouteResult] = []
    for index, request in enumerate(requests):
        arrival = request["timestamp"]
        while events and events[0][0] <= arrival:
            _, _, worker, blocks = heapq.heappop(events)
            caches[worker].access(blocks)
        length = request["input_length"]
        hits = [min(length, cache.match(request["hash_ids"]) * block_size) for cache in caches]
        waits = [max(0, ready - arrival) for ready in available]
        # Integer time units: compute costs 4/token; cached KV reads cost read_cost/token.
        service = [(length - hit) * 4 + hit * read_cost for hit in hits]
        # Ties go to the least recently assigned worker, identically for both policies.
        if policy == "random":
            worker = rng.randrange(workers)
        elif policy == "least-loaded":
            worker = min(range(workers), key=lambda w: (waits[w], last_assigned[w]))
        elif policy == "cache-aware":
            worker = min(range(workers), key=lambda w: (waits[w] + service[w], last_assigned[w]))
        else:
            raise ValueError(f"Unknown policy: {policy}")
        finish = arrival + waits[worker] + service[worker]
        available[worker] = finish
        last_assigned[worker] = index
        heapq.heappush(events, (finish, index, worker, request["hash_ids"]))
        rows.append({"worker": worker, "hit_tokens": hits[worker], "ttft": finish - arrival})
    return rows


def workload(seed: int, prefixes: int, spacing: float, count: int = REQUESTS) -> list[Request]:
    """Each request: one of `prefixes` first blocks, then a shared 3-block suffix."""
    rng = random.Random(seed)
    return [
        {
            "timestamp": i * spacing,
            "input_length": 16,
            "hash_ids": [rng.randrange(prefixes) if prefixes else 1000 + i, 10, 11, 12],
        }
        for i in range(count)
    ]
