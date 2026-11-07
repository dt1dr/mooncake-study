"""Fetch explicitly selected, commit-pinned traces and verify their SHA256."""

import argparse
import hashlib
import json
import tempfile
import urllib.request
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent


def fetch(entry: dict[str, Any], destination: Path, *, allow_large: bool = False) -> Path:
    limit = entry["size_bytes"]
    if limit > 2_000_000_000 and not allow_large:
        raise ValueError("Downloads over 2 GB require --allow-large")
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / entry["filename"]
    if target.exists():
        digest = hashlib.sha256()
        with target.open("rb") as existing:
            for chunk in iter(lambda: existing.read(1024 * 1024), b""):
                digest.update(chunk)
        if target.stat().st_size == limit and digest.hexdigest() == entry["sha256"]:
            return target
        raise ValueError(f"Existing file has a different checksum; move it aside first: {target}")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination, delete=False) as output:
            temporary = Path(output.name)
            digest = hashlib.sha256()
            size = 0
            with urllib.request.urlopen(entry["url"], timeout=30) as response:
                while chunk := response.read(1024 * 1024):
                    size += len(chunk)
                    if size > limit:
                        raise ValueError("Download exceeded the manifest's expected size")
                    digest.update(chunk)
                    output.write(chunk)
        if size != limit or digest.hexdigest() != entry["sha256"]:
            raise ValueError("Trace size or SHA256 mismatch")
        temporary.replace(target)
        return target
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", nargs="?", help="Manifest entry; omitted to list available traces")
    parser.add_argument("--allow-large", action="store_true")
    args = parser.parse_args()
    entries = json.loads((HERE / "manifest.json").read_text())["files"]
    if args.name is None:
        for name, entry in entries.items():
            print(f"{name}: {entry['size_bytes']} bytes ({entry['paper_version']})")
        return 0
    if args.name not in entries:
        parser.error(f"Unknown trace: {args.name}")
    print(fetch(entries[args.name], HERE / "raw", allow_large=args.allow_large))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
