"""Run the six-step Store acceptance with isolated native processes."""

import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from contextlib import ExitStack
from pathlib import Path
from typing import Any

from common.artifacts import write_summary
from env.check_env import check_track, collect_report


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def listening(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.2):
            return True
    except OSError:
        return False


def wait_for(
    ready: Callable[[], bool], process: subprocess.Popen[bytes], seconds: float, name: str
) -> None:
    deadline = time.monotonic() + seconds
    while not ready():
        if process.poll() is not None or time.monotonic() > deadline:
            raise RuntimeError(f"{name} not ready; see results/{name}.log")
        time.sleep(0.1)


def stop(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
    process.wait(timeout=5)


def main(directory: Path) -> int:
    errors = check_track(collect_report(), "linux-cpu")
    if errors:
        print("not tested: " + "; ".join(errors))
        return 3
    results = directory / "results"
    results.mkdir(exist_ok=True)
    processes: list[subprocess.Popen[bytes]] = []
    metrics: dict[str, Any] = {}
    with ExitStack() as stack, tempfile.TemporaryDirectory() as temporary:

        def launch(name: str, args: list[str]) -> subprocess.Popen[bytes]:
            log = stack.enter_context((results / f"{name}.log").open("w"))
            process = subprocess.Popen(
                args,
                stdin=subprocess.PIPE,
                stdout=log,
                stderr=log,
                env=os.environ
                | {
                    "GLOG_logtostderr": "1",
                    "MC_STORE_MEMCPY": "0",
                    "MC_STORE_CLIENT_SETUP_RETRIES": "1",
                },
            )
            processes.append(process)
            stack.callback(stop, process)
            return process

        def client(mode: str, address: str, port: int = 0) -> tuple[subprocess.Popen[bytes], Path]:
            output = Path(temporary) / f"{mode}.json"
            process = launch(
                mode,
                [
                    sys.executable,
                    str(directory / "src/client.py"),
                    mode,
                    address,
                    str(output),
                    str(port),
                ],
            )
            return process, output

        port = free_port()
        address = f"127.0.0.1:{port}"
        master = launch(
            "master",
            [
                shutil.which("mooncake_master"),
                f"--rpc_port={port}",
                f"--metrics_port={free_port()}",
                "--metrics_host=127.0.0.1",
                "--enable_offload=false",
            ],
        )
        wait_for(lambda: listening(port), master, 20, "master")
        metrics["master_ready"] = True
        writer, output = client("writer", address)
        wait_for(output.exists, writer, 30, "writer")
        metrics["writer"] = json.loads(output.read_text())
        log = (results / "writer.log").read_text()
        match = re.search(r"TcpTransport: listen on port (\d+)", log)
        if match is None or metrics["writer"].get("put_code") != 0:
            raise RuntimeError("Writer put/TCP initialization failed; see results/writer.log")
        tcp_port = int(match[1])
        reader, reader_output = client("reader", address, tcp_port)
        reader.wait(timeout=30)
        metrics["reader"] = json.loads(reader_output.read_text())
        writer.communicate(input=b"close\n", timeout=20)
        metrics["writer"] = json.loads(output.read_text())
        after, after_output = client("after", address, tcp_port)
        after.wait(timeout=30)
        metrics["after"] = json.loads(after_output.read_text())
        # Keep a bound, non-listening socket so no other service can take this endpoint.
        with socket.socket() as unused:
            unused.bind(("127.0.0.1", 0))
            invalid, invalid_output = client("invalid", f"127.0.0.1:{unused.getsockname()[1]}")
            invalid.wait(timeout=45)
            metrics["invalid"] = json.loads(invalid_output.read_text())
    metrics["cleanup"] = all(p.poll() is not None for p in processes)
    print(json.dumps(metrics, indent=2))
    return write_summary(directory, metrics, {"tcp-store": list(metrics)})
