import copy
import shutil
from pathlib import Path

import pytest

from common.artifacts import read_summary
from common.cli import invoke, run_lab


@pytest.mark.integration
def test_tcp_acceptance(tmp_path):
    lab = Path(__file__).resolve().parents[1]
    directory = tmp_path / lab.name
    shutil.copytree(lab, directory, ignore=shutil.ignore_patterns("results", "__pycache__"))
    assert run_lab(directory) == 0
    summary = read_summary(directory)
    assert invoke(directory, "verify", summary) == 0
    corrupted = copy.deepcopy(summary)
    corrupted["metrics"]["reader"]["tcp_received_bytes"] = 0
    assert invoke(directory, "verify", corrupted) == 1
