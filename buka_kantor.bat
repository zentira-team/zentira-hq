@echo off
cd /d "%~dp0"
title Zentira HQ - Kantor Virtual 3D Multi-Agent AI

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment .venv belum ditemukan di folder ini.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" main.py office
if errorlevel 1 (
    echo.
    echo [ERROR] Server Kantor 3D berhenti dengan kesalahan.
    pause
)
