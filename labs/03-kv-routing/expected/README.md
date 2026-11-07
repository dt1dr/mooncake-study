# Expected evidence

No external numerical reference exists for this simplified model. The expectations are
the hypotheses registered in `lab.yaml` before the run on seeds 200–209:

- NC1: cache-aware and least-loaded make identical decisions with identical TTFT
  statistics, and every policy has zero hit tokens.
- (a) cache-aware has lower total TTFT than least-loaded in every seed at spacing 24, 32, 48.
- (b) exactly equal with unique prefixes, zero capacity, or read cost 4.
- (c) the seed-averaged gap is largest at 4 prefixes (vs. 2, 8, 16) and at capacity 8
  (vs. 4, 16), and shrinks as read cost goes 1, 2, 4.

Unit tests count small two-worker examples by hand: completion-time visibility, queueing,
cache-aware reuse, and least-recently-assigned tie-breaking.
