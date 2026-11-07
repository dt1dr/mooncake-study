# mooncake-study

Runnable study notes for [Mooncake](https://github.com/kvcache-ai/Mooncake), the
KVCache-centric serving system behind Kimi ([FAST'25 paper](https://www.usenix.org/system/files/fast25-qin.pdf)).
Four small CPU experiments cover KV cache size, prefix reuse on the official traces,
cache-aware routing, and moving bytes through Mooncake Store. Each lab points to the
paper section or upstream source at a pinned commit, and checks its own results.

You need Python and a rough idea of what a KV cache is; no GPU or model weights.
This is an independent study project, not part of Mooncake, and its simulations say
nothing about Mooncake's full-system performance.

## Quick start

With [uv](https://docs.astral.sh/uv/getting-started/installation/) installed, from the
repository root on Linux, macOS or Windows:

```sh
uv sync --locked
uv run --locked --offline --no-sync python -m common.cli run 01
uv run --locked --offline --no-sync python -m common.cli verify 01
```

`verify` should print `passed: lab01, 8 cases match the official calculator exactly`.
Results are written to `labs/01-kv-memory/results/summary.json`.

Python 3.12 or 3.13. On WSL, keep the repository in the Linux filesystem (`~/...`), not
under `/mnt/c`, where file access is slow.

## Labs

Work through 01 → 02 → 03; 04 stands alone.

| Lab | Question | What you check |
| --- | --- | --- |
| [01 · KV memory](labs/01-kv-memory/README.md) | How do context length and KV heads change memory use? | Exact byte counts against the official calculator |
| [02 · Prefix reuse](labs/02-trace-reuse/README.md) | When can a cached prefix be reused, and what does eviction change? | Hand-built traces and the official hit-rate/capacity curve |
| [03 · KV-aware routing](labs/03-kv-routing/README.md) | When does cache locality outweigh queue load? | TTFT across a parameter sweep, with a no-reuse control |
| [04 · TCP Store](labs/04-mooncake-store/README.md) | Can another process read the stored bytes, and who owns them? | Byte equality, TCP counters and what happens when the writer exits |

Lab 02 needs the paper's Conversation trace (about 3 MB, downloaded once; see
[data/README.md](data/README.md)). After that, run and verify it like lab 01:

```sh
uv run --locked --offline --no-sync python data/fetch.py conversation
uv run --locked --offline --no-sync python -m common.cli run 02
uv run --locked --offline --no-sync python -m common.cli verify 02
```

Lab 03 needs nothing extra. Lab 04 needs Linux x86_64 (WSL2 works), glibc ≥ 2.35 and
the optional Mooncake CPU wheel:

```sh
uv sync --locked --group mooncake
uv run --locked --offline --no-sync python env/check_env.py --track linux-cpu
uv run --locked --offline --no-sync python -m common.cli run 04
uv run --locked --offline --no-sync python -m common.cli verify 04
```

## Commands

With Make: `make sync`, `make check`, `make lab-01`, `make verify-01`, and
`make sync-store` / `make check-store` for lab 04. Without Make, use the
`uv run ... python -m common.cli check | run NN | verify NN` form shown above.

`run` replaces the lab's previous `summary.json`; a failed run leaves none behind.
`verify` only reads saved results and never reruns an experiment.
Exit codes: 0 ok, 1 failed, 3 not tested (missing data or results, unsupported
platform). Make reports any nonzero exit as 2.

## Further reading

- [Paper → source → lab map](notes/paper-map.md): which claims each lab checks, and to what level.
- [Reproducibility rules](notes/reproducibility.md): what counts as evidence here.

## Contributing

Issues and PRs are welcome, especially for wrong claims, unclear explanations or a lab
that fails on your machine (include the command, its output and your OS). Before a PR,
run `make check` and verify the lab you touched; Store changes also need `make check-store`.
A new claim goes into the lab's `lab.yaml` before you implement or run it; see
[Reproducibility rules](notes/reproducibility.md).

## License

Original code and documentation are [MIT](LICENSE). Upstream code, traces and papers
keep their own licenses.

## 中文概要

用四个 CPU 小实验读 Mooncake 论文：KV cache 大小、官方 trace 上的前缀复用、缓存感知路由，
以及通过 Mooncake Store 跨进程传输数据。每个实验都对应论文章节或固定版本的上游源码，并自带
结果校验。不需要 GPU 和模型权重：先按 Quick start 跑通 lab01，再按 01 → 02 → 03 往下做；
04 需要 Linux。
