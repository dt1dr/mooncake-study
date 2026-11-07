"""Collect an offline environment report using only the standard library."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import re
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = (
    "pyyaml",
    "jsonschema",
    "pytest",
    "ruff",
    "matplotlib",
    "torch",
    "mooncake-transfer-engine-non-cuda",
    "mooncake-transfer-engine",
    "mooncake-transfer-engine-cuda13",
)


def command(args: list[str], timeout: int = 10) -> dict[str, Any]:
    try:
        result = subprocess.run(
            args, cwd=ROOT, capture_output=True, text=True, timeout=timeout, check=False
        )
        return {"returncode": result.returncode, "output": (result.stdout + result.stderr).strip()}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"returncode": None, "output": str(exc)}


def package_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for name in PACKAGES:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return versions


def collect_report() -> dict[str, Any]:
    git = command(["git", "rev-parse", "HEAD"])
    status = command(["git", "status", "--porcelain"])
    lock = ROOT / "uv.lock"
    smi = shutil.which("nvidia-smi")
    if not smi and Path("/usr/lib/wsl/lib/nvidia-smi").is_file():
        smi = "/usr/lib/wsl/lib/nvidia-smi"
    report: dict[str, Any] = {
        "collected_at": datetime.now(UTC).isoformat(),
        "python": platform.python_version(),
        "platform": platform.system(),
        "machine": platform.machine(),
        "kernel": platform.release(),
        "wsl": "microsoft" in platform.release().lower(),
        "libc": list(platform.libc_ver()),
        "packages": package_versions(),
        "tools": {name: command([name, "--version"]) for name in ("uv", "nvcc")},
        "gpus": command(
            [
                smi,
                "--query-gpu=name,driver_version,memory.total,compute_cap",
                "--format=csv,noheader,nounits",
            ]
        )
        if smi
        else None,
        "git_sha": git["output"] if git["returncode"] == 0 else None,
        "git_dirty": bool(status["output"]) if status["returncode"] == 0 else None,
        "uv_lock_sha256": hashlib.sha256(lock.read_bytes()).hexdigest() if lock.exists() else None,
        "warnings": [],
    }
    if str(ROOT).startswith("/mnt/") and report["wsl"]:
        report["warnings"].append("Keep this repository in the WSL Linux filesystem, e.g. ~/src.")
    if report["git_sha"] is None:
        report["warnings"].append(
            "Git revision unavailable; source revision will be recorded as null."
        )
    stable = {k: v for k, v in report.items() if k not in {"collected_at", "warnings"}}
    report["fingerprint"] = hashlib.sha256(json.dumps(stable, sort_keys=True).encode()).hexdigest()
    return report


def check_track(report: dict[str, Any], track: str) -> list[str]:
    errors = []
    version = tuple(int(v) for v in report["python"].split(".")[:2])
    if not (3, 12) <= version < (3, 14):
        errors.append("Use Python 3.12 or 3.13; default: uv sync --locked (3.13.17).")
    flavors = [
        name for name in PACKAGES if name.startswith("mooncake-") and report["packages"][name]
    ]
    if len(flavors) > 1:
        errors.append(f"Conflicting Mooncake wheels share one namespace: {', '.join(flavors)}.")
    if track == "linux-cpu":
        if report["platform"] != "Linux" or report["machine"] != "x86_64":
            errors.append("lab04 targets Linux x86_64 (including WSL2).")
        libc, value = report["libc"]
        numbers = tuple(int(v) for v in re.findall(r"\d+", value)[:2])
        if libc != "glibc" or numbers < (2, 35):
            errors.append("Project Linux baseline requires glibc >= 2.35 (Ubuntu 22.04+).")
        if not report["packages"]["mooncake-transfer-engine-non-cuda"]:
            errors.append("Install the CPU wheel with: uv sync --locked --group mooncake.")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--track", choices=["portable-cpu", "linux-cpu"], default="portable-cpu")
    parser.add_argument("--output", type=Path, default=ROOT / "env_report.json")
    args = parser.parse_args()
    report = collect_report()
    report["track"] = args.track
    report["errors"] = check_track(report, args.track)
    report["status"] = "failed" if report["errors"] else "passed"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"{report['status']}: {args.track}; report: {args.output}")
    for message in report["warnings"] + report["errors"]:
        print(message)
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
