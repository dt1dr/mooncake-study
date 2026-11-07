# Tested environments

These are local test records, not a compatibility guarantee. Dependency versions come
from the committed `uv.lock`; selection reasons are in [toolchains.md](toolchains.md).

| Date | Platform | Python | Checks executed |
| --- | --- | --- | --- |
| 2026-10-29 | WSL2 x86_64, glibc 2.43 | 3.12.16 / 3.13.17 | CPU tests and lab03 sweep verification |
| 2026-11-07 | WSL2 x86_64, glibc 2.43 | 3.13.17 | 44 CPU tests, Store acceptance, labs 01–04 run and verified at clean commit `3dffadd`, with Mooncake CPU wheel 0.3.13.post1 |

Lab01 also ran and verified in a source copy without `.git`, using the existing Python
environment. This checks ZIP-style execution, not installation on a fresh machine.

Fresh WSL installation, macOS/Windows and remote CI acceptance remain open.
GPU integrations have not been tested. Published claim levels are in the
[paper map](../notes/paper-map.md).
