"""Portable command interface behind Makefile; usable from native Windows too."""

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

from jsonschema import ValidationError
from yaml import YAMLError

from common.artifacts import NOT_TESTED, read_summary
from common.metadata import ROOT, check_repository, lab_directories, lab_directory, load_lab


def invoke(directory: Path, name: str, *args: object) -> int:
    path = directory / "src" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"lab_{directory.name[:2]}_{name}", path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.main(directory, *args)


def verify_lab(directory: Path) -> int:
    summary = read_summary(directory)
    if summary is None:
        print(f"not tested: {directory.name}")
        return NOT_TESTED
    # The envelope is not experimental evidence: a lab-specific verifier is mandatory.
    return invoke(directory, "verify", summary)


def run_lab(directory: Path) -> int:
    """Replace previous evidence; an incomplete run must leave no verifiable summary."""
    summary = directory / "results/summary.json"
    summary.unlink(missing_ok=True)
    code = 1
    try:
        code = invoke(directory, "run")
        return code
    finally:
        if code != 0:
            summary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["check", "schema", "run", "verify"])
    parser.add_argument("lab", nargs="?")
    args = parser.parse_args(argv)
    try:
        if args.action == "schema":
            return check_repository()
        if args.action == "check":
            for command in (
                [sys.executable, "-m", "ruff", "check", "."],
                [sys.executable, "-m", "ruff", "format", "--check", "."],
                [sys.executable, "-m", "common.cli", "schema"],
                [sys.executable, "-m", "pytest"],
            ):
                result = subprocess.run(command, cwd=ROOT, check=False)
                if result.returncode:
                    return result.returncode
            return 0
        if args.lab is None:
            parser.error("run/verify requires a lab ID")
        if args.action == "verify" and args.lab == "all":
            codes = [verify_lab(directory) for directory in lab_directories()]
            return 1 if 1 in codes else NOT_TESTED if NOT_TESTED in codes else 0
        directory = lab_directory(args.lab)
        load_lab(directory)
        if args.action == "verify":
            return verify_lab(directory)
        return run_lab(directory)
    except (ValueError, OSError, ValidationError, YAMLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
