#!/usr/bin/env bash
# scripts/check-spec.sh — POSIX shim for the SDD gate.
# Allows: ./scripts/check-spec.sh  or  bash scripts/check-spec.sh
# Forwards all args to the Python wrapper.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python "${SCRIPT_DIR}/check-spec.py" "$@"
