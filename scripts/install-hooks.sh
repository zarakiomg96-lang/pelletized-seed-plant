#!/usr/bin/env bash
# scripts/install-hooks.sh — one-time local hook installer (POSIX).
#
# Idempotent: re-running on a clone that already has the hook wired is
# effectively a no-op (still re-applies the chmod bit + reports the
# current core.hooksPath value). Safe to invoke from onboarding docs,
# a Makefile, or a fresh shell.
#
# What it does (cross-platform semantics baked in):
#   1. chmod +x on .githooks/pre-commit (POSIX file mode bit; Windows
#      ignores this step because Git invokes scripts via shebang).
#   2. `git config core.hooksPath .githooks` (cross-platform: tells Git
#      to look in the version-controlled `.githooks/` directory for
#      hooks, replacing the per-clone default `.git/hooks/`).
#
# Reference: SPEC.md §15.3.1 item 16 + docs/PRE-COMMIT.md §6.

set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

HOOK_FILE=".githooks/pre-commit"
HOOKS_DIR_REL=".githooks"

# Sanity check: the version-controlled hook must live here. If it's
# missing, the user has not pulled v2.4 yet — error loud, don't fake-fix.
if [ ! -f "$HOOK_FILE" ]; then
    echo "::error::$HOOK_FILE not found in the working tree. Pull the v2.4 changes first (or `git fetch && git checkout` to pick up the migration)." >&2
    exit 1
fi

# (1) chmod +x — POSIX-only step. On Windows, Git invokes scripts via
# the shebang line and does not require any file mode bit, so the chmod
# either no-ops or errors silently; either way it's harmless.
chmod +x "$HOOK_FILE" 2>/dev/null || true
echo "[install-hooks] chmod +x $HOOK_FILE"

# (2) git config core.hooksPath — cross-platform, points Git at the
# version-controlled hooks directory. Idempotency check first so we
# don't blindly overwrite a non-default value the user may have set
# intentionally.
CURRENT="$(git config --get core.hooksPath || true)"
if [ "$CURRENT" = "$HOOKS_DIR_REL" ]; then
    echo "[install-hooks] core.hooksPath already set to '$HOOKS_DIR_REL' (no-op)"
else
    git config core.hooksPath "$HOOKS_DIR_REL"
    echo "[install-hooks] git config core.hooksPath '$HOOKS_DIR_REL'"
fi

# (3) Smoke-test: invoke the hook on empty staging to confirm it runs.
echo ""
echo "[install-hooks] OK. Verifying install via empty-staging smoke test:"
if bash "$HOOK_FILE" </dev/null; then
    echo "[install-hooks] Empty-staging smoke test passed (silent exit 0)."
else
    echo "::error::Empty-staging smoke test of $HOOK_FILE failed. Investigate before your next commit." >&2
    exit 1
fi

echo ""
echo "[install-hooks] Future commits will run $HOOK_FILE automatically."
echo "[install-hooks] Verify with:  git config core.hooksPath   (should print: .githooks)"
