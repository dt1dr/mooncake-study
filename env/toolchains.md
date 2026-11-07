# Toolchain choices

- **Python 3.12–3.13**: 3.12 is the project's minimum; 3.13 is the newest version with
  a Mooncake 0.3.13.post1 wheel (cp310–cp313).
  `.python-version` selects the default; actual test runs are in [versions.md](versions.md).
- **uv** manages dependencies with the committed `uv.lock`. Experiments use
  `--locked --offline --no-sync` after installation so they do not change the environment.
- **Matplotlib** renders lab02 and lab03 plots with the headless Agg backend.
- **Mooncake 0.3.13.post1**, CPU wheel, is optional and used only by lab04. The source
  anchors in each lab refer to the corresponding pinned release.

All Mooncake wheel flavors share the `mooncake` namespace. Install only one flavor in
an environment; the environment checker detects conflicting installations.

Lab04 targets Linux x86_64 and requires glibc ≥ 2.35 as a project support boundary.
That boundary is not a claim that every qualifying system has been tested; consult the
[tested combinations](versions.md). The labs use prebuilt wheels and need no compiler.
GPU engine dependencies will be selected when a GPU lab is implemented.
