#!/usr/bin/env python3
"""
scripts/check-spec.py — portable entry point around spec-lint.py.

Use this from CI, pre-commit hooks, IDEs, or just from the shell when you
want a human-friendly wrapper:

    python scripts/check-spec.py             # run the gate
    python scripts/check-spec.py --json      # machine-readable
    python scripts/check-spec.py --quiet     # only summary line

The script delegates to ../spec-lint.py and propagates the exit code, so it
is safe to wire into any workflow that runs on file change or before commit.

Works on Windows / macOS / Linux with the system Python (>= 3.8).

Reference:
    SPEC.md §15.3.1 — contract that the gate enforces.
    SPEC.md §15.3   — how to write a new validator for a BUG-* or PEND-*.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SPEC_LINT = os.path.join(ROOT, "spec-lint.py")


def _run(args: list[str], capture: bool) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, SPEC_LINT, *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run spec-lint.py (the SDD gate) and propagate its exit code. "
            "See SPEC.md §15.3.1 for the contract that the gate enforces."
        )
    )
    parser.add_argument(
        "--json", action="store_true",
        help="forward --json to spec-lint.py for machine-readable output",
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="suppress the gate table; only print the one-line summary",
    )
    args = parser.parse_args()

    forward: list[str] = []
    if args.json:
        forward.append("--json")

    # Both --quiet and --json need to capture the gate's stdout/stderr:
    # --quiet so the table is discarded and only our summary line shows;
    # --json so we control how the JSON is forwarded (the wrapper itself
    # must NEVER write anything to stdout before or after the JSON).
    capture_table = args.quiet or args.json

    # In default mode we print a banner. In --quiet / --json modes we keep the
    # stdout stream pristine for downstream consumers (their parsers).
    if not capture_table and not args.json:
        print(f"[check-spec] running {os.path.relpath(SPEC_LINT, ROOT)} "
              f"in {ROOT}")
    rc, stdout_text, stderr_text = _run(forward, capture=capture_table)

    # When the user asked for --json (and possibly --quiet), still emit the
    # JSON payload so pipes can consume it.
    if args.json:
        # --json mode: pipes expect a valid JSON document on stdout, nothing
        # else. Forward the gate's stdout (and stderr for diagnostics) but do
        # NOT print any wrapper summary — that would corrupt the stream for
        # downstream parsers.
        sys.stdout.write(stdout_text)
        sys.stderr.write(stderr_text)
        return rc

    if args.quiet:
        # Quieter mode: discard the gate table (captured above) and emit
        # exactly one summary line so the caller can branch on PASS / FAIL.
        if rc == 0:
            print("[check-spec] PASS — exit 0 (gate verde)")
        else:
            print(f"[check-spec] FAIL — exit {rc}")
        return rc

    # Default mode: stream the table through (just streamed by subprocess)
    # and add a multi-line resolution guide under it.
    if rc == 0:
        print()
        print("[check-spec] gate verde. SDD pipeline: edit → spec → gate → "
              "merge.")
    else:
        print()
        print("[check-spec] gate ROTO. Próximos pasos:")
        print("   1. Releer las líneas [FAIL] arriba.")
        print("   2. Editar HTML/CSS/JS o la spec según corresponda.")
        print("   3. Re-correr `python spec-lint.py` hasta exit 0.")
        print("   4. Anotar el bug nuevo en SPEC.md §14 antes de mergear.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
