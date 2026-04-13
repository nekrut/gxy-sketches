#!/usr/bin/env bash
# Regenerate every sketch from scratch. Requires ANTHROPIC_API_KEY.
set -euo pipefail

cd "$(dirname "$0")/.."

uv run gxy-sketches ingest iwc
uv run gxy-sketches ingest nf-core

uv run gxy-sketches generate --source iwc --overwrite
uv run gxy-sketches generate --source nf-core --overwrite

uv run gxy-sketches validate
