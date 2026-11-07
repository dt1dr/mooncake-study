# Expected evidence

`hand-traces.json` is the input and hand-derived reference for Part A, under the
leaf-LRU conventions in the lab README. Each scenario starts with an empty cache and
uses 4-token blocks. NC1 expects zero for every request.

| Scenario | Reasoning |
| --- | --- |
| shared-prefix | The extended request reuses blocks 1–2; the shorter successor reuses both again. |
| divergent-prefix | `[1,5,3]` after `[1,2,3]` reuses only block 1: block 3 under a different parent is a different prefix. Repeating `[1,5,3]` then hits all three. |
| lru-refresh | Capacity 2. Reusing 1 makes 2 the victim when 3 arrives; 2 then misses and evicts 1, so 3 still hits. |
| partial-tail | A 6-token request stores a full block and a 2-token tail; repeating it hits 6 tokens. A 3-token request with ID 1 hits one block but counts only its 3 tokens. |
| request-exceeds-cache | Capacity 2 with 3-block requests: the first evicts its own tail and keeps block 1; the second hits block 1 (protected) and again evicts its own tail. |
| zero-capacity | Nothing is stored. |

`official-curve.json` records Part B's settings and independent reference counts,
captured from the [official Python simulator](https://github.com/kvcache-ai/kvcache-blog/tree/7d449d1fe1a5419af90c554f222e025dcc3756ba/packages/kvcache-simulator)
at `7d449d1fe1a5419af90c554f222e025dcc3756ba`, using the Conversation file pinned in
[`data/manifest.json`](../../../data/manifest.json). The upstream implementation was
run outside this repository; it is not a project dependency.

To recapture from a separate checkout of that commit, expose its
`packages/kvcache-simulator/src` on `PYTHONPATH`, then run:

```sh
python -m kvcache_sim run --trace /path/to/conversation_trace.jsonl \
  --model llama-3.1-70b --kv-precision bf16_fp16 --block-size 512 \
  --policies lru --backend python --no-progress --format json
```

The pinned defaults supply the budgets and 50% warmup. The snapshot retains model
accounting and exact `hitTokens`, request/window counts and `totalMeasuredTokens` from
that output. Hit rates and capacity in blocks are derived, not separately stored.
NC1 expectations are zero; they are not part of the official snapshot. Verification
reads these references and saved metrics without loading raw traces or replaying them.
