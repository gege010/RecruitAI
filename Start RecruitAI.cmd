@echo off
setlocal
where py >nul 2>&1
if not errorlevel 1 (
    py -3.11 -c "import sys" >nul 2>&1
    if not errorlevel 1 (
        py -3.11 "%~dp0run_local.py" %*
        goto :finished
    )
    py -3.12 -c "import sys" >nul 2>&1
    if not errorlevel 1 (
        py -3.12 "%~dp0run_local.py" %*
        goto :finished
    )
)
where python >nul 2>&1
if errorlevel 1 (
    echo Pasang Python 3.11 atau 3.12, lalu jalankan kembali Start RecruitAI.
    pause
    exit /b 1
)
python "%~dp0run_local.py" %*
:finished
set "result=%errorlevel%"
if not "%result%"=="0" pause
exit /b %result%
