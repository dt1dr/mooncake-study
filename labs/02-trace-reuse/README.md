# Lab 02: Trace prefix reuse

## 1. Goal

A: verify longest-prefix matching, finite-capacity eviction and hit-token counting on hand-built traces. B: reproduce the official hit-rate/capacity curve on the pinned trace. Both parts use one cache model, `common/prefix_cache.py`, which follows the official simulator.

## 2. Paper correspondence

[FAST'25](https://www.usenix.org/system/files/fast25-qin.pdf) §3.2.1, §5.3. Claims are registered in [`lab.yaml`](lab.yaml).

## 3. Prerequisites

Linux, macOS or Windows; Python 3.12/3.13 after `uv sync --locked`. No GPU. Prior labs: 01.
Runtime: a few seconds. Download the pinned Conversation trace (about 3 MB) once;
everything after that runs offline.

## 4. Run

```sh
uv run --locked --offline --no-sync python data/fetch.py conversation  # one-time download
make lab-02       # or: uv run --locked --offline --no-sync python -m common.cli run 02
make verify-02    # checks existing results only
```

## 5. Expected output

| Convention | Both parts (official Python backend) |
| --- | --- |
| Identity | Prefix-tree edges: a block ID only matches under the same parent path |
| Lookup | Longest cached prefix from the root; touched left to right |
| Blocks | Partial tails occupy one slot and count their actual input tokens |
| Eviction | Least-recent leaf only; the hit prefix is protected during admission, newly inserted nodes are not |
| Data and order | Part A: six hand traces, 4-token blocks, budgets in blocks. Part B: SHA256-checked Conversation trace, all 12,031 requests in file order, 512-token blocks, Llama 3.1 70B BF16, floor(GiB × 2³⁰ / bytes per block) slots |
| Window | Part A: every request. Part B: first floor(N/2) requests warm up; a budget not filled by then is omitted with all larger ones |
| Metric | Hit tokens per request (A) or measured hit tokens / measured input tokens (B) |
| NC1 | Each ID becomes `(request_index, id)`; timestamps, lengths, order and within-request identity are kept. Every NC1 hit count must be zero |

Part A saves per-request `hit_tokens` and `nc1_hit_tokens`; expected values and their
derivation are in [`expected/`](expected/README.md). Part B saves the sweep under
`metrics.official-curve` and draws `results/curve.png` (replay, official reference, NC1).
`make verify-02` compares all saved counts exactly, without replaying.

The captured curve has 14 points (1–8192 GiB); 16384 GiB is underfilled. For example,
1024 GiB saves 10,394,228 of 67,915,607 measured input tokens (15.30%).

## 6. Differences from the paper

The model is serial: no request overlap, Store allocation, replicas or latency. Part B
compares the pinned official tool's output, not a paper figure with other settings.
Counting partial tails follows the trace model; it does not show that an engine can
reuse incomplete KV blocks.

## 7. Further reading

- [`FAST25-release/README.md`](https://github.com/kvcache-ai/Mooncake/blob/719735896c86b56fabec6cf3e825fb2ea640597a/FAST25-release/README.md) @ `719735896c86`
- [`FAST25-release/traces/conversation_trace.jsonl`](https://github.com/kvcache-ai/Mooncake/blob/719735896c86b56fabec6cf3e825fb2ea640597a/FAST25-release/traces/conversation_trace.jsonl) @ `719735896c86`
- [KVCache.AI Python simulator](https://github.com/kvcache-ai/kvcache-blog/tree/7d449d1fe1a5419af90c554f222e025dcc3756ba/packages/kvcache-simulator)
- [Reproducibility rules](../../notes/reproducibility.md)
