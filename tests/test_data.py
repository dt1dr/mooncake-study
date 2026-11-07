import hashlib
import io

import pytest

from data.fetch import fetch


def entry():
    return {
        "filename": "test.jsonl",
        "size_bytes": 3,
        "sha256": hashlib.sha256(b"abc").hexdigest(),
        "url": "https://example.invalid/trace",
    }


def test_checked_download_and_cache(tmp_path, monkeypatch):
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: io.BytesIO(b"abc"))
    assert fetch(entry(), tmp_path).read_bytes() == b"abc"
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: pytest.fail("cache hit fetched"))
    assert fetch(entry(), tmp_path).read_bytes() == b"abc"


@pytest.mark.parametrize("payload", [b"bad", b"too large", b"a"])
def test_bad_download_never_becomes_artifact(tmp_path, monkeypatch, payload):
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: io.BytesIO(payload))
    with pytest.raises(ValueError):
        fetch(entry(), tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_large_download_requires_explicit_flag(tmp_path):
    value = entry()
    value["size_bytes"] = 2_000_000_001
    with pytest.raises(ValueError, match="allow-large"):
        fetch(value, tmp_path)
