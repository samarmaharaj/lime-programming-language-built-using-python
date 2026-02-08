@echo off
REM Lime Programming Language Launcher
REM This batch file ensures the proper Python environment is activated before running Lime

REM Check if we're in a conda environment
if defined CONDA_DEFAULT_ENV (
    echo Using conda environment: %CONDA_DEFAULT_ENV%
) else (
    REM Try to activate the lime environment
    echo Activating conda environment...
    call conda activate lime
    if errorlevel 1 (
        echo Error: Could not activate lime conda environment
        echo Please ensure conda is installed and the 'lime' environment exists
        echo You can create it with: conda create -n lime python=3.12
        pause
        exit /b 1
    )
)

REM Run the Python script directly
python "%~dp0main.py" %*

REM Pause to see output if run by double-clicking
if "%1"=="" pause