#!/bin/sh
# scripts/smoke-site.sh — POSIX wrapper for the runtime probe.
#
# Passes every argument through to smoke-site.py. Use this from CI, git
# hooks, or any POSIX shell that requires shebang `.sh` for portability.
#
# Usage:    sh scripts/smoke-site.sh [--json]
exec python "$(dirname "$0")/smoke-site.py" "$@"
