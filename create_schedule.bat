@echo off
setlocal enabledelayedexpansion

:: Deteksi apakah virtual environment lokal ada
if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
    echo Menggunakan Python dari Virtual Environment: !PYTHON_EXE!
) else (
    set "PYTHON_EXE=C:\Python314\python.exe"
    echo Virtual environment tidak ditemukan. Menggunakan Python Global: !PYTHON_EXE!
)

echo Mendaftarkan tugas otomatisasi di Windows Task Scheduler...
schtasks /create /tn "ImportSahamPostgres" /tr "\"!PYTHON_EXE!\" \"%~dp0auto_import.py\"" /sc daily /st 09:00 /f
if %errorlevel% equ 0 (
    echo ============================================================
    echo [SUCCESS] Sinyal otomatisasi berhasil didaftarkan!
    echo Impor database akan berjalan setiap hari pada jam 09:00 pagi.
    echo ============================================================
) else (
    echo ============================================================
    echo [ERROR] Gagal mendaftarkan tugas. 
    echo Harap jalankan file .bat ini dengan cara klik kanan dan
    echo pilih "Run as Administrator".
    echo ============================================================
)
pause
