# Lab 04: Mooncake Store over TCP

## 1. Goal

Store and retrieve byte objects between separate processes with `MooncakeDistributedStore` over TCP.

## 2. Paper correspondence

[FAST'25](https://www.usenix.org/system/files/fast25-qin.pdf) §3.2.2. Claims are registered in [`lab.yaml`](lab.yaml).

## 3. Prerequisites

Linux x86_64 or WSL2, glibc ≥ 2.35, `uv sync --locked --group mooncake`. No GPU or RDMA.
Prior labs: none. Runtime: about 10 seconds.

## 4. Run

```sh
make lab-04       # or: uv run --locked --offline --no-sync python -m common.cli run 04
make verify-04    # checks existing results only
```

## 5. Expected output

The runner launches an isolated master and separate writer/reader processes. It uses
P2PHANDSHAKE metadata, a 64 MiB writer segment and 16 MiB local buffers. Readers mount
no segment, so the writer owns the only stored replica. No external service is needed.

1. Wait for the master's RPC listener; client setup then checks API readiness.
2. Writer puts 1 MiB of bytes generated with seed 42 and stays alive.
3. Reader checks every byte against its independently generated payload. With
   `MC_STORE_MEMCPY=0`, Linux `TCP_INFO.tcpi_bytes_received` on connections to the
   writer's logged TCP data port must increase by at least the payload size.
4. Writer calls `close()` and exits. A fresh reader must retrieve an empty result:
   removing the sole mounted segment removes this object's backing storage.
5. Setup against a bound, non-listening local endpoint must return a nonzero code, and
   the wheel's own log (`results/invalid.log`) must contain an error from
   `master_client.cpp`. On 0.3.13.post1 it reads `Client not available`, without the
   master address.
   `MC_STORE_CLIENT_SETUP_RETRIES=1` bounds this failure experiment.
6. All child processes are reaped in a cleanup block, including on exceptions;
   native calls have subprocess deadlines and terminate/kill fallback.

`results/summary.json` contains bytes, equality, TCP counters, lifecycle results and
process IDs. Native logs remain beside it. `make verify-04` reads this evidence only.
`make check-store` runs this acceptance experiment in a temporary directory.
No raw payload is written to disk.

## 6. Differences from the paper

Functional check only; no KV cache semantics and no bandwidth claim (RDMA is NR).
Lifecycle coverage is graceful writer shutdown with one replica and no offload; crash
recovery, replicas and persistence are outside this experiment.

## 7. Further reading

- [`mooncake-wheel/tests/test_distributed_object_store.py`](https://github.com/kvcache-ai/Mooncake/blob/719735896c86b56fabec6cf3e825fb2ea640597a/mooncake-wheel/tests/test_distributed_object_store.py) @ `719735896c86`
- [`mooncake-transfer-engine/src/transport/tcp_transport/tcp_transport.cpp`](https://github.com/kvcache-ai/Mooncake/blob/719735896c86b56fabec6cf3e825fb2ea640597a/mooncake-transfer-engine/src/transport/tcp_transport/tcp_transport.cpp) @ `719735896c86`
- [Reproducibility rules](../../notes/reproducibility.md)
