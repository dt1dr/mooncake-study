# Reproducibility boundaries

Each claim has its own **target level**, **observed level**, and independent execution
**status**. Current statuses and observed levels are listed in `paper-map.md`.

| Level | Evidence scope | Permitted statement |
| --- | --- | --- |
| L0 | Mechanism or functionality | “Demonstrates how X works.” |
| L1 | Relative trend over stated parameters | “Within this simulation's range, X improves Y.” |
| L2 | Same data, metric and conventions | “Matches the published value under matching conditions.” |
| NR | Required infrastructure unavailable | Cite the source and state the missing resources. |

Levels describe evidence types, not a ranking. An exact formula may directly support L2.
Statuses are `pending`, `observed`, `not-tested`; status must never be inferred from level.
An environment smoke check, successful import or valid JSON is not an observed lab claim.

NC1 removes **cross-request** reuse by giving each request its own block-ID namespace,
preserving arrival time, lengths and within-request identity. Global one-to-one renaming
preserves sharing and is invalid. Lab03 must use identical deterministic tie-breaking
for least-loaded and cache-aware routing so their NC1 outputs can be compared exactly.

External comparison aligns block size, budget, eviction policy, statistical window and
request ordering. FAST'25 and historical arXiv traces are separate datasets. An analysis
on the same trace with a different metric is independent analysis, not L2.

Claim status and levels are recorded once, in `lab.yaml`; `results/summary.json` carries
the environment report (fingerprint, lockfile SHA256, Git SHA) and per-claim evidence.
Randomized experiments record the seeds they actually use in their metrics.
Git metadata is optional: ZIP downloads record a null revision. It describes source
provenance, not experimental success. Summaries contain evidence, without a claim status.
A completed run saves a summary; the lab verifier determines whether its evidence passes.
Raising an `observed_level` requires a verified run at a clean Git commit
(`git_dirty: false`); record that commit in `paper-map.md`.
The summary schema checks the envelope; a lab-specific verifier checks the science.
`verify` never reruns an experiment or creates missing evidence.

Cache/transfer evidence must include bytes, hit blocks or saved prefill tokens. Lab04
must additionally demonstrate TCP transport. Quantiles and variation across repeated
runs are required for timing comparisons. Unsupported GPU experiments are not tested.
RDMA bandwidth and full-system cluster throughput remain NR on this baseline.
