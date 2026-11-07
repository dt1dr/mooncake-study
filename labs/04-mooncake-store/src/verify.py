"""Verify saved byte, TCP, lifecycle and cleanup evidence; never start services."""

import re
from pathlib import Path
from typing import Any


def main(directory: Path, summary: dict[str, Any]) -> int:
    metrics = summary["metrics"]
    writer, reader = metrics["writer"], metrics["reader"]
    after, invalid = metrics["after"], metrics["invalid"]
    results = directory / "results"
    match = re.search(r"TcpTransport: listen on port (\d+)", (results / "writer.log").read_text())
    # The pinned wheel's own diagnostic, not a message written by client.py. It names the
    # failing master client but not the address, so the address is not required here.
    native_error = re.search(
        r"^E\d{4} .*master_client\.cpp:\d+\] .+$", (results / "invalid.log").read_text(), re.M
    )
    checks = {
        "master readiness": metrics["master_ready"],
        "distinct processes": writer["pid"] != reader["pid"],
        "successful setup/close": all(
            r.get("setup_code") == 0 and r.get("close_code") == 0 and "error" not in r
            for r in (writer, reader, after)
        ),
        "put/get equality": writer.get("put_code") == 0
        and reader.get("equal") is True
        and reader.get("bytes") == 2**20,
        "TCP data path": match is not None
        and reader.get("tcp_peer_port") == int(match[1])
        and reader.get("tcp_received_bytes", 0) >= 2**20,
        "writer exit lifecycle": after.get("bytes") == 0 and after.get("equal") is False,
        "invalid master diagnosis": invalid.get("setup_code", 0) != 0 and native_error is not None,
        "process cleanup": metrics["cleanup"],
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        print("failed: " + ", ".join(failed))
        return 1
    print(
        "passed: lab04 cross-process TCP bytes, writer-exit lifecycle, invalid master and cleanup"
    )
    return 0
