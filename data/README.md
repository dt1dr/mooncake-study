# Trace staging

`manifest.json` records commit-pinned official URLs, byte sizes and SHA256 digests.
Raw data is ignored. Nothing is fetched by `make check` or by the lab runners.

```sh
uv run --locked --offline --no-sync python data/fetch.py
uv run --locked --offline --no-sync python data/fetch.py conversation
```

The second command explicitly enables network I/O in the downloader; `uv --offline`
only prevents uv from accessing a package index. Repeated downloads validate the existing
file. Corrupt files are rejected and never silently overwritten. Lab runners also reject
a staged file whose SHA256 differs from the manifest.

Use conversation/toolagent/synthetic for FAST'25 and `arxiv` for the older report.
Do not substitute one release for the other when comparing reference numbers.
All have 512-token blocks per the pinned upstream release README. Preserve file order
and record the statistical window, cache budget and eviction policy in each experiment.
