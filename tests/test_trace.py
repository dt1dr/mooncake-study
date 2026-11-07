import hashlib
import json

import pytest

from common.trace import load_trace


def test_staged_trace_preserves_file_order_and_checks_checksum(tmp_path, monkeypatch):
    monkeypatch.setattr("common.trace.ROOT", tmp_path)
    data = tmp_path / "data"
    (data / "raw").mkdir(parents=True)
    requests = [
        {"timestamp": 2, "input_length": 2, "hash_ids": [1]},
        {"timestamp": 1, "input_length": 2, "hash_ids": [1]},
    ]
    content = "\n".join(json.dumps(r) for r in requests).encode()
    entry = {"filename": "toy.jsonl", "sha256": hashlib.sha256(content).hexdigest()}
    (data / "manifest.json").write_text(json.dumps({"files": {"toy": entry}}))
    with pytest.raises(FileNotFoundError, match="data/fetch.py toy"):
        load_trace("toy")
    path = data / "raw/toy.jsonl"
    path.write_bytes(content)
    assert load_trace("toy") == requests
    path.write_bytes(content + b"\n")
    with pytest.raises(ValueError, match="SHA256"):
        load_trace("toy")
