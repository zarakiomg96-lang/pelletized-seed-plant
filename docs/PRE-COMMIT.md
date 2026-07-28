# `docs/PRE-COMMIT.md` — Operative guide for the pre-commit hook

The SDD gate runs as a git pre-commit hook at `.git/hooks/pre-commit`.
This doc explains what it does, when it triggers, and how a human
operator extends it. For drift-detection runtime proofs (group #14 of
the gate) see `docs/RUNTIME-PROOFS.md`. For the spec-side contract see
`docs/GATE-CONTRACT.md item 16` and `CHANGELOG.md v2.2`.

## 1. Why it exists

Pre-commit hooks are the cheapest place to catch drift: the developer
is still in the loop, the commit hasn't shipped, and a `[FAIL]` row
blocks the commit before the change lands. Without this hook, drift
between `sitemap.xml`, the served HTML, and the HTML's `<a href>`
graph ships to CI and triggers a slower feedback loop — or worse, a
user clicks the broken link in production. The hook closes the loop
at commit time → essentially free for trivial edits, <30 s for full
edits, blocks drift before any merge attempt.

## 2. Mechanism

The hook is a POSIX bash script (3-step pipeline):

1. `git diff --cached --name-only --diff-filter=ACMR` → list of staged
   paths (added/copied/modified/renamed; deletes drop out).
2. Classify each path against the trivial whitelist (see §3). If ANY
   path falls outside → `SCOPE=full`; otherwise `SCOPE=fast`.
3. Invoke `python scripts/check-spec.py --scope=$SCOPE --quiet` with
   `--timeout=30` only when `SCOPE=fast`.
4. Propagate the gate's exit code: 0 = commit proceeds, 1 = drift
   blocked, 124 = timeout blocked. On failure, print a resolution
   message + `git commit --no-verify` bypass hint.

The hook is **read-only** — it never touches the working tree or the
index. A `[FAIL]` only blocks the commit, never corrupts state.

## 3. Scope decision: trivial vs full

Trivial whitelist (case-sensitive per `grep -E` default; the project
standardizes on lowercase directory names):

| Path prefix / exact | Why trivial |
|---|---|
| `docs/` | Operator-facing documentation (`RUNTIME-PROOFS.md`, this file, …) |
| `scripts/` | The gate tooling itself + its POSIX/Windows wrappers |
| `SPEC.md` | The specification of record |
| `README.md` | Project readme |
| `.gitignore` | Repo plumbing |

Anything else — `.html`, `.css`, `.js`, `sitemap.xml`, `.json`,
`package.json`, new files under any other directory — ranks as
content → `SCOPE=full` → all 15 gate groups run.

**Why fast skips only group #14 (runtime proofs)**: that group boots
its own HTTP server on a `127.0.0.1` port (one of `4321-4330`) and
runs `urllib` round-trips on every sitemap URL — slow (1-2 s) and
correctness-equivalent under docs-only edits (the sitemap never moves
on a docs-only commit, so if the gate was green at the start of the
commit it is still green at the end).

**Why fast keeps group #15 (byte budget)**: that group compresses
every HTML + asset with `gzip.compress` and asserts aggregate weight
under budget. It is sub-second even on the full asset set, and catches
egregious regressions (a 50 MB image accidentally added under `docs/`
of all places, say) before the commit even tries the merge.

## 4. Timeout

The fast lane caps at 30 seconds via
`subprocess.run(timeout=30, start_new_session=True)` in
`scripts/check-spec.py`. On expiry:

1. `subprocess.TimeoutExpired` is raised in the wrapper.
2. The wrapper calls `os.killpg(os.getpgid(exc.pid), signal.SIGTERM)`
   — reaps the **entire process group**, not just the gate child.
3. Returns exit code 124 (convention from `bash timeout`) with a clear
   stderr message (`"[pre-commit] gate exceeded 30s timeout"`).

The whole-tree kill is non-negotiable for cross-platform safety:
without `start_new_session=True` + killpg, an outer 30 s timeout
firing on a gate that internally launched `smoke-site.py` would leave
the smoke-site alive with its `http.server` daemon thread still
bound to ports `4321-4330`. Subsequent fast-lane commits would
find those ports held and burn their own 30 s budget rotating
through `PORT_CANDIDATES`. With killpg, the port is released
immediately on timeout.

The full lane has no implicit timeout — `scripts/check-spec.py` is
called without `--timeout` so the gate runs until absorbed by the
machine's own CPU/time budget. CI scripts that invoke the gate
manually can pass `--timeout=N` to put their own ceiling on it.

## 5. Bypass

For WIP commits where the gate is failing and you genuinely need to
land a snapshot before fixing:

```
git commit --no-verify
```

This is Git's native hook-bypass mechanism — it skips every
pre-commit hook, not just this one. The hook prints the hint in its
FAIL message so it's discoverable. **Never** `--no-verify` ship to
merged branches: the gate is there for a reason. Recommended only
for throwaway commits you intend to amend or rebase later.

## 6. Install (per clone)

> **v2.4.1 — preferred install path**: one-shot wrapper scripts handle **everything** described below in a single call, including the `git config`, the optional POSIX `chmod +x`, a sanity check (errors out loud if `.githooks/pre-commit` is missing), and an empty-staging smoke test. They are idempotent (safe to re-run) and cross-platform:
>
> ```bash
> # POSIX (Linux / macOS / Git Bash on Windows):
> bash scripts/install-hooks.sh
>
> # Windows (cmd or PowerShell):
> scripts\install-hooks.bat
> ```
>
> After install, `git config core.hooksPath` returns `.githooks` and future commits are gated by `.githooks/pre-commit` automatically. The **manual commands below remain valid as a fallback** for users who prefer not to invoke wrappers, but the wrappers are the recommended path.

The hook source-of-truth now lives at `.githooks/pre-commit` (a
**versioned** location, tracked in the repo). The default location
`.git/hooks/` is per-clone and NOT versioned; we use Git's
`core.hooksPath` indirection to point Git at the versioned copy.

```bash
# After `git clone`, run ONCE per clone:
git config core.hooksPath .githooks

# On Windows only — if the file lost its +x bit in the clone:
chmod +x .githooks/pre-commit

# Verify the indirection is set:
git config --get core.hooksPath
# expected: .githooks

# Smoke-test on empty staging:
bash .githooks/pre-commit
# expected: exit 0 silently (STAGED empty → early return)
```

After `core.hooksPath` is set, every `git pull` automatically picks
up updates to `.githooks/pre-commit` — the install procedure is
**one-time per clone**, not per-version. Future edits to the hook
land in the repo via normal commits; no copy-paste, no extra `chmod`.

Why this is better than the old `.git/hooks/` pattern: previously
every new clone needed the bytes re-pasted manually plus a
`chmod +x` — a step easy to forget on rushed commits, and silently
skipped if a developer clones-and-commits in one minute. With
`core.hooksPath`, the hook is part of the repo: same checkout,
same hook, drift impossible.

**Caveats**:

- **Windows developers**: Git's mode-preservation isn't 100%
  reliable across Windows-native checkouts; you may need a one-time
  `chmod +x .githooks/pre-commit` after the first clone.
- **Old clones**: if you have an existing clone that used the
  `.git/hooks/pre-commit` pattern, just run `git config
  core.hooksPath .githooks` once. The old file in `.git/hooks/`
  becomes dead bytes; safe to delete or ignore.
- **Fresh clones, no config yet**: if a developer clones and runs
  `git commit` BEFORE running the `git config` one-liner, the hook
  silently does nothing. Mitigation: surface this in onboarding
  docs or wrap it in a `make bootstrap` target.

See docs/GATE-CONTRACT.md item 16 for the contract side. See CHANGELOG.md v2.4
for the changelog row that introduced this pattern.

## 7. Cross-references

- `docs/RUNTIME-PROOFS.md` — runtime proofs (group #14) mechanics,
  port allocator (`4321-4330`), drift categories
  (`declared-not-served` / `served-but-unlisted`), smoke-site.py
  walkthrough for when you add a process 08.
- `docs/GATE-CONTRACT.md item 16` — gate contract side of pre-commit
  wiring (matches this doc 1:1).
- `CHANGELOG.md v2.2` — when this hook landed + the cadence of
  contracts to update if you bump the trivial whitelist or the 30 s
  cap.
- `scripts/check-spec.py` — wrapper that exposes `--scope` +
  `--timeout` flags this hook consumes. Searches for `killpg` /
  `start_new_session` inside this file to see the timeout cleanup
  chain.
- `spec-lint.py → SCOPE_GROUPS` — module-level dict that maps
  `--scope={fast,full}` to the indices of `ALL_CHECKS` to skip.
  Indices are 0-based so `SCOPE_GROUPS["fast"] = {13}` skips the
  14th function in the tuple (= group #14, `check_runtime_proofs`).
