# Lab 01: KV memory footprint

## 1. Goal

Derive KV cache size from a model config and check it against the official calculator. Standard MHA/GQA only; MLA, sliding-window and hybrid models are out of scope.

## 2. Paper correspondence

[FAST'25](https://www.usenix.org/system/files/fast25-qin.pdf) §2.2, Table 1. Claims are registered in [`lab.yaml`](lab.yaml).

## 3. Prerequisites

Linux, macOS or Windows; Python 3.12/3.13 after `uv sync --locked`. No GPU, model weights
or network access. Prior labs: none. Runtime: a few seconds.

## 4. Run

```sh
make lab-01       # or: uv run --locked --offline --no-sync python -m common.cli run 01
make verify-01    # checks existing results only
```

## 5. Expected output

Formula: `2 × layers × kv_heads × head_dim × tokens × bytes_per_element × batch`.
Inputs are the standard attention fields of the official calculator's Llama 3.1 model
presets. The runner uses these fields to calculate bytes independently; the verifier
compares saved results against the [archived calculator outputs](expected/README.md).

| Case | GiB |
| --- | ---: |
| 70B, BF16, 8192 tokens | 2.5 |
| 70B, BF16, 32768 tokens | 10 |
| 70B, BF16, 128000 tokens | 39.0625 |
| 70B, BF16, 131072 tokens | 40 |
| 8B, BF16, 131072 tokens | 16 |
| 70B, 1-byte KV elements, 131072 tokens | 20 |
| 70B, BF16, 131072 tokens, two sequences | 80 |
| 70B dimensions with 64 KV heads (MHA counterfactual) | 320 |

The console shows bytes, decimal GB and binary GiB; `results/summary.json` saves them.
40 GiB equals 42.94967296 GB. Here `128k` means 131072; the 128000 case is separate.
Exact bytes and unit conversions must match for all eight cases.

## 6. Differences from the paper

Only the KV payload is counted: no weights, allocator overhead, quantization scales,
padding or distributed sharding. The 1-byte case is a storage-size calculation, not an
accuracy experiment. The MHA counterfactual changes only KV heads; it is not a released
Llama configuration.

## 7. Further reading

- [`README.md`](https://github.com/kvcache-ai/Mooncake/blob/719735896c86b56fabec6cf3e825fb2ea640597a/README.md) @ `719735896c86`
- [Reproducibility rules](../../notes/reproducibility.md)
