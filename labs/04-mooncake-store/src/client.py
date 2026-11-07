"""Isolated native Store client, launched by run.py (never imported by CPU tests)."""

import json
import os
import random
import socket
import struct
import sys
from pathlib import Path
from typing import Any

from mooncake.store import MooncakeDistributedStore


def received_bytes(port: int) -> int:
    total = 0
    for path in Path("/proc/self/fd").iterdir():
        try:
            if not path.readlink().as_posix().startswith("socket:"):
                continue
            with socket.socket(fileno=os.dup(int(path.name))) as connection:
                if connection.family == socket.AF_INET and connection.getpeername()[1] == port:
                    # Linux tcp_info: 104-byte prefix, then pacing rates, bytes_acked,
                    # bytes_received. This field is available on the Linux baseline.
                    info = connection.getsockopt(socket.IPPROTO_TCP, socket.TCP_INFO, 136)
                    total += struct.unpack_from("=Q", info, 128)[0]
        except OSError:
            continue
    return total


def main() -> None:
    mode, address, output, port = sys.argv[1:]
    store = MooncakeDistributedStore()
    result: dict[str, Any] = {"pid": os.getpid(), "seed": 42}
    try:
        code = store.setup(
            "127.0.0.1",
            "P2PHANDSHAKE",
            64 * 2**20 if mode == "writer" else 0,
            16 * 2**20,
            "tcp",
            "",
            address,
        )
        result["setup_code"] = code
        if code == 0 and mode == "writer":
            data = random.Random(result["seed"]).randbytes(2**20)
            result["put_code"] = store.put("lab04-payload", data)
            publish(output, result)
            sys.stdin.readline()
        elif code == 0 and mode in ("reader", "after"):
            before = received_bytes(int(port))
            data = store.get("lab04-payload")
            result.update(
                tcp_peer_port=int(port),
                bytes=len(data),
                equal=data == random.Random(result["seed"]).randbytes(2**20),
                tcp_received_bytes=received_bytes(int(port)) - before,
            )
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        result["close_code"] = store.close()
    publish(output, result)


def publish(output: str, result: dict[str, Any]) -> None:
    path = Path(output)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(result))
    temporary.replace(path)


if __name__ == "__main__":
    main()
