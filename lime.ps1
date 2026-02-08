# Lime Programming Language Launcher
# PowerShell wrapper to ensure proper environment setup

param(
    [Parameter(Position=0, Mandatory=$true)]
    [string]$SourceFile,
    
    [Parameter(Position=1, ValueFromRemainingArguments=$true)]
    [string[]]$AdditionalArgs
)

# Check if we're in a conda environment
if ($env:CONDA_DEFAULT_ENV) {
    Write-Host "Using conda environment: $env:CONDA_DEFAULT_ENV" -ForegroundColor Green
} else {
    Write-Host "Activating conda environment 'lime'..." -ForegroundColor Yellow
    
    # Try to activate the lime environment
    try {
        & conda activate lime
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to activate environment"
        }
    } catch {
        Write-Error "Could not activate lime conda environment"
        Write-Host "Please ensure conda is installed and the 'lime' environment exists" -ForegroundColor Red
        Write-Host "You can create it with: conda create -n lime python=3.12" -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Build the argument list
$pythonArgs = @("$PSScriptRoot\main.py", $SourceFile) + $AdditionalArgs

# Run the Python script
& python @pythonArgs

# Display exit code if non-zero
if ($LASTEXITCODE -ne 0) {
    Write-Host "Process exited with code: $LASTEXITCODE" -ForegroundColor Red
}