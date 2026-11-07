# Lab 03: KV-aware routing

## 1. Goal

Compare random, least-loaded and cache-aware routing in a small deterministic simulator inspired by Conductor.

## 2. Paper correspondence

[FAST'25](https://www.usenix.org/system/files/fast25-qin.pdf) §4. Claims are registered in [`lab.yaml`](lab.yaml).

## 3. Prerequisites

Linux, macOS or Windows; Python 3.12/3.13 after `uv sync --locked`. No GPU. Prior labs: 02.
Runtime: a few seconds.

## 4. Run

```sh
make lab-03       # or: uv run --locked --offline --no-sync python -m common.cli run 03
make verify-03    # checks existing results only
```

## 5. Expected output

Model (`common/routing.py`):

- Two FIFO workers, each with a prefix-tree LRU cache (`common/prefix_cache.py`).
- Compute costs 4 time units/token; cached KV reads cost `read_cost` units/token, a local
  read cost, not network transfer. TTFT = queue wait + prefill service time.
- Lookup at arrival is read-only; a request's blocks are admitted when it completes.
- least-loaded minimizes queue wait; cache-aware minimizes queue wait + service time
  (the design's load + α × miss cost). Ties go to the least recently assigned worker for
  both, so without reuse they make identical decisions.
- Workload: 120 requests, 16 tokens each: one of `prefixes` first blocks plus a shared
  3-block suffix, arriving every `spacing` units.

The sweep changes one factor at a time around the baseline (4 prefixes, 8-block caches,
spacing 32, read cost 1); spacing 32 saturates both workers when every request misses.
It runs over held-out seeds 200–209 and repeats every scenario under NC1. For each seed it
saves total TTFT, p50/p95, SLO hits (TTFT ≤ 64), makespan and hit tokens; NC1 also saves
every worker decision. `results/sensitivity.png` shows the mean TTFT saved by cache-aware
routing as prefix count, cache capacity and read cost change, with the range across seeds.
`make verify-03` checks complete sweep coverage, NC1 equality and the registered
hypothesis (a)–(c) in `lab.yaml` from these values, without rerunning.

Rationale for (c): cache-aware routing should matter most when one worker's cache cannot
hold the hot prefixes but the two caches together can (4 prefixes × 4 blocks vs. 8 blocks
per worker). With fewer prefixes or larger caches, every worker can hold everything.

## 6. Differences from the paper

| Aspect | This simulator | Conductor |
| --- | --- | --- |
| Cache state | Finite per-worker prefix blocks | Distributed catalog, replica migration |
| Cost | Load + α × missing-prefix cost | Full production cost model |
| Scheduling | Three deterministic policies, fixed tie-breaking | PD placement, early rejection |
| Service time | Queue + prefill and local KV read cost | Real GPU timings, continuous batching |

Simulator trends do not establish the paper's end-to-end throughput gains (NR).

## 7. Further reading

- [`docs/source/design/conductor/conductor-architecture-design.md`](https://github.com/kvcache-ai/Mooncake/blob/719735896c86b56fabec6cf3e825fb2ea640597a/docs/source/design/conductor/conductor-architecture-design.md) @ `719735896c86`
- [Reproducibility rules](../../notes/reproducibility.md)
