@echo off
:: ─────────────────────────────────────────────────────────────
::  franz.bat  —  FranzCode Launcher for Windows
::
::  INSTALL (one-time setup):
::    1. Add the franzcode\ folder to your System PATH:
::       Search "Edit the system environment variables"
::       → Environment Variables → Path → Edit → New
::       → Enter full path to franzcode\
::    2. Now you can type:  franz  from anywhere!
::
::  USAGE:
::    franz                  → Interactive REPL
::    franz myfile.franz     → Run a file
::    franz --ast myfile.franz
::    franz --tokens myfile.franz
:: ─────────────────────────────────────────────────────────────

setlocal

:: Find Python
where python >nul 2>&1
if %errorlevel% equ 0 (
    set PY=python
) else (
    where python3 >nul 2>&1
    if %errorlevel% equ 0 (
        set PY=python3
    ) else (
        echo FranzCode requires Python 3. Download from https://python.org
        exit /b 1
    )
)

:: Get the directory of this batch file
set SCRIPT_DIR=%~dp0

:: Run main.py, pass all arguments through
%PY% "%SCRIPT_DIR%main.py" %*
