@echo off
rem scripts/smoke-site.bat — Windows wrapper for the runtime probe.
rem
rem Passes every argument through to smoke-site.py. Use this from cmd.exe,
rem Task Scheduler, Git for Windows hooks, or any Windows-native runner
rem that requires a .bat surface.
rem
rem Usage:    scripts\smoke-site.bat [--json]
python "%~dp0smoke-site.py" %*
