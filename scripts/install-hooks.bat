@echo off
REM scripts\install-hooks.bat — one-time local hook installer (Windows).
REM
REM Idempotent: re-running on a clone that already has the hook wired
REM is effectively a no-op (reports the current value, no overwrite).
REM
REM What it does (Windows-specific semantics):
REM   1. (no chmod — Windows does not have POSIX file mode bits; Git
REM      invokes scripts via shebang regardless of any +x bit, so the
REM      Windows version needs nothing here.)
REM   2. `git config core.hooksPath .githooks` (cross-platform: tells
REM      Git to look in the version-controlled `.githooks/` directory
REM      for hooks).
REM
REM Reference: docs/GATE-CONTRACT.md item 16 + docs/PRE-COMMIT.md §6.

setlocal

pushd "%~dp0\.."

REM Sanity check: the version-controlled hook must be present. If it's
REM missing, the user hasn't pulled v2.4 yet — error loud, no fake-fix.
if not exist ".githooks\pre-commit" (
    echo ::error::.githooks\pre-commit not found in the working tree. Pull the v2.4 changes first.
    exit /b 1
)

REM (2) git config core.hooksPath — cross-platform. Idempotency check
REM first to avoid clobbering any value the user may have set
REM intentionally.
for /f "delims=" %%i in ('git config --get core.hooksPath') do set CURRENT=%%i
if "%CURRENT%"==".githooks" (
    echo [install-hooks] core.hooksPath already set to '.githooks' ^(no-op^)
) else (
    git config core.hooksPath .githooks
    echo [install-hooks] git config core.hooksPath .githooks
)

REM (3) Smoke-test on empty staging.
echo.
echo [install-hooks] OK. Verifying install via empty-staging smoke test:
bash .githooks\pre-commit
if errorlevel 1 (
    echo ::error::Empty-staging smoke test of .githooks\pre-commit failed. Investigate before your next commit.
    exit /b 1
)
echo [install-hooks] Empty-staging smoke test passed ^(silent exit 0^).

echo.
echo [install-hooks] Future commits will run .githooks\pre-commit automatically.
echo [install-hooks] Verify with:  git config core.hooksPath   ^(should print: .githooks^)

popd
exit /b 0
