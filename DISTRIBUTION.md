# Lime Programming Language - Distribution Guide

## Running Lime Programs

### Option 1: Batch File (Windows CMD)
Use the `lime.bat` file to run Lime programs from Command Prompt:
```cmd
lime.bat tests\ifAndBoolean.lime
lime.bat path\to\your\program.lime
```

### Option 2: PowerShell Script (Windows PowerShell)
Use the `lime.ps1` file to run Lime programs from PowerShell:
```powershell
.\lime.ps1 tests\ifAndBoolean.lime
.\lime.ps1 path\to\your\program.lime --debug-compiler
```

### Option 3: Directory Distribution
You can also use the packaged executable in the `dist` folder:
```cmd
dist\lime\lime.exe tests\ifAndBoolean.lime
```

Note: The directory distribution may have issues with LLVM dependencies on different machines.

### Option 4: Direct Python Execution
If you have Python and the required dependencies installed:
```cmd
python main.py tests\ifAndBoolean.lime
```

## Requirements

- **For Batch/PowerShell Scripts**: 
  - Conda environment named 'lime' with Python 3.12
  - Required packages: llvmlite, and other dependencies from requirements.txt

- **For Directory Distribution**: 
  - May work standalone but could have LLVM dependency issues on different machines

## Environment Setup

To set up the conda environment:
```cmd
conda create -n lime python=3.12
conda activate lime
pip install -r requirements.txt
```

## Recommended Usage

For the most reliable experience, use either `lime.bat` (for CMD) or `lime.ps1` (for PowerShell). These ensure the proper Python environment is activated before running your Lime programs.

## Files Structure

- `lime.bat` - Windows batch file launcher
- `lime.ps1` - PowerShell script launcher  
- `dist/lime/` - Directory distribution with executable
- `main.py` - Main Lime interpreter
- `tests/` - Example Lime programs
- `assets/lime_icon.ico` - Icon file used for executable