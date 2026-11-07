"""Validate lab metadata and result envelopes without downloading anything."""

import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


def validate(document: dict[str, Any], schema: str) -> None:
    definition = json.loads(
        (ROOT / "schemas" / f"{schema}.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator(definition).validate(document)


def load_lab(directory: Path) -> dict[str, Any]:
    metadata = yaml.safe_load((directory / "lab.yaml").read_text(encoding="utf-8"))
    validate(metadata, "lab")
    ids = [claim["id"] for claim in metadata["claims"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Claim IDs must be unique within a lab")
    if metadata["cache_benefit"] and "NC1" not in metadata["negative_controls"]:
        raise ValueError("Cache-benefit labs require NC1 with per-request independent block IDs")
    if directory.name != f"{metadata['id']}-{metadata['name']}":
        raise ValueError("Lab directory and metadata ID/name differ")
    return metadata


def lab_directories(root: Path = ROOT) -> list[Path]:
    return sorted((root / "labs").glob("[0-9][0-9]-*"))


def lab_directory(lab_id: str, root: Path = ROOT) -> Path:
    matches = list((root / "labs").glob(f"{lab_id}-*"))
    if len(matches) != 1:
        raise ValueError(f"Unknown or ambiguous lab: {lab_id}")
    return matches[0]


def check_repository(root: Path = ROOT) -> int:
    directories = lab_directories(root)
    if not directories:
        raise ValueError("No labs found")
    labs = []
    for directory in directories:
        labs.append(load_lab(directory))
        for name in ("README.md", "run.sh", "src/run.py", "src/verify.py", "tests", "expected"):
            if not (directory / name).exists():
                raise ValueError(f"Missing {directory.name}/{name}")
        headings = [
            line
            for line in (directory / "README.md").read_text(encoding="utf-8").splitlines()
            if line.startswith("## ")
        ]
        if len(headings) != 7:
            raise ValueError(f"{directory.name}: README must have exactly seven sections")
    lab_ids = {metadata["id"] for metadata in labs}
    for metadata in labs:
        if not set(metadata["depends_on"]) <= lab_ids or metadata["id"] in metadata["depends_on"]:
            raise ValueError(f"Invalid dependencies for {metadata['id']}")
    print(f"Validated {len(labs)} lab manifests and directory contracts")
    return 0
