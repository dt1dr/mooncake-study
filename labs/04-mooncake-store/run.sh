#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/../.."
exec "${UV:-uv}" run --locked --offline --no-sync python -m common.cli run 04 "$@"
