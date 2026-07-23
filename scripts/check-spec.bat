@echo off
REM scripts/check-spec.bat — Windows shim for the SDD gate.
REM Allows: check-spec  (from any directory)
REM Forwards all args to the Python wrapper.

setlocal
set "SCRIPT_DIR=%~dp0"
python "%SCRIPT_DIR%check-spec.py" %*
endlocal
