# Paper → source → lab map

Observed levels below were accepted by each lab's verifier on results produced at commit
`adfd9db` (Python 3.13.17, WSL2 x86_64). Source snapshot:
[`v0.3.13.post1`, `719735896c86b56fabec6cf3e825fb2ea640597a`](https://github.com/kvcache-ai/Mooncake/tree/719735896c86b56fabec6cf3e825fb2ea640597a).
This is the official release tag, cut on a short post-release line from `main`, so it is
not an ancestor of `main`; it matches the pinned 0.3.13.post1 wheel.
These are reading anchors, not assertions that the present implementation is identical
to the system evaluated in the paper. FAST'25 sections refer to
[the USENIX PDF](https://www.usenix.org/system/files/fast25-qin.pdf).

| Claim / topic | Source | Lab | Target | Status / observed |
| --- | --- | --- | --- | --- |
| Standard MHA/GQA KV memory footprint | FAST'25 §2.2 / Table 1; [upstream README](https://github.com/kvcache-ai/Mooncake/blob/719735896c86b56fabec6cf3e825fb2ea640597a/README.md) | 01 | L2 | observed / L2 |
| Contiguous prefix hits and finite-capacity eviction | FAST'25 §3.2.1; [trace format](https://github.com/kvcache-ai/Mooncake/blob/719735896c86b56fabec6cf3e825fb2ea640597a/FAST25-release/README.md) | 02-A | L0 | observed / L0 |
| Official trace hit-rate/capacity comparison | FAST'25 §5.3; [conversation trace](https://github.com/kvcache-ai/Mooncake/blob/719735896c86b56fabec6cf3e825fb2ea640597a/FAST25-release/traces/conversation_trace.jsonl) | 02-B | L2 | observed / L2 |
| Simplified cache-aware routing degenerates under NC1 | Study hypothesis inspired by FAST'25 §4; [Conductor design](https://github.com/kvcache-ai/Mooncake/blob/719735896c86b56fabec6cf3e825fb2ea640597a/docs/source/design/conductor/conductor-architecture-design.md) | 03 | L0 | observed / L0 |
| Simulated routing trends over a stated workload range | Study hypothesis inspired by FAST'25 §4; same source anchor | 03 | L1 | observed / L1 |
| TCP Store cross-process byte equality | FAST'25 §3.2.2 topic; [Python API usage tests](https://github.com/kvcache-ai/Mooncake/blob/719735896c86b56fabec6cf3e825fb2ea640597a/mooncake-wheel/tests/test_distributed_object_store.py); [TCP implementation](https://github.com/kvcache-ai/Mooncake/blob/719735896c86b56fabec6cf3e825fb2ea640597a/mooncake-transfer-engine/src/transport/tcp_transport/tcp_transport.cpp) | 04 | L0 | observed / L0 |
| Transfer Engine segment/batch interface | FAST'25 §3.2.2; [header](https://github.com/kvcache-ai/Mooncake/blob/719735896c86b56fabec6cf3e825fb2ea640597a/mooncake-transfer-engine/include/transfer_engine.h) | 04 extension | L0 | not-tested / null |
| PD transfer and shared prefix reuse | FAST'25 §3.1; vLLM connectors (M3 version not selected) | future 06a/06b/07 | L0/L1 | not-tested / null |
| Cluster throughput, production request capacity, RDMA bandwidth | Original paper version and hardware must be cited individually | none | NR | not-tested / null |

The arXiv technical report, FAST'25 and ToS versions have different section numbering
and evaluation results. In particular, the 525% / 75% figures belong
to the arXiv-era report; do not relabel them as FAST'25 findings. This repository does
not reproduce either version's whole-system performance numbers.

Reference outputs and capture instructions: [lab01 calculator](../labs/01-kv-memory/expected/README.md)
and [lab02 LRU curve](../labs/02-trace-reuse/expected/README.md). Model, unit and token-count
conventions are documented in [lab01](../labs/01-kv-memory/README.md#5-expected-output);
cache and measurement conventions in [lab02](../labs/02-trace-reuse/README.md#5-expected-output).

Update this table only after the relevant lab's scientific verifier accepts its artifacts.
