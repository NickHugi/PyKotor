# PowerShell script to set up development environment
# Usage: .\scripts\setup_dev_environment.ps1

param(
    [switch]$SkipPreCommit,
    [switch]$SkipVenv,
    [string]$VenvName = ".venv"
)

Write-Host "Setting up PyKotor development environment..." -ForegroundColor Green

# Check Python installation
Write-Host "`nChecking Python installation..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}
Write-Host "Found: $pythonVersion" -ForegroundColor Green

# Create virtual environment
if (-not $SkipVenv) {
    Write-Host "`nCreating virtual environment..." -ForegroundColor Yellow
    if (Test-Path $VenvName) {
        Write-Host "Virtual environment already exists at $VenvName" -ForegroundColor Yellow
    } else {
        python -m venv $VenvName
        Write-Host "Virtual environment created at $VenvName" -ForegroundColor Green
    }
    
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & "$VenvName\Scripts\Activate.ps1"
}

# Upgrade pip
Write-Host "`nUpgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip setuptools wheel

# Install development dependencies
Write-Host "`nInstalling development dependencies..." -ForegroundColor Yellow
pip install -e Libraries/PyKotor
pip install -e Libraries/PyKotorGL
pip install -e Libraries/PyKotorFont
pip install -e .[dev]

# Install pre-commit hooks
if (-not $SkipPreCommit) {
    Write-Host "`nInstalling pre-commit hooks..." -ForegroundColor Yellow
    pip install pre-commit
    pre-commit install
    Write-Host "Pre-commit hooks installed" -ForegroundColor Green
}

# Verify installation
Write-Host "`nVerifying installation..." -ForegroundColor Yellow
python -c "import pykotor; print('✓ PyKotor installed')"
python -c "import pykotor.gl; print('✓ PyKotorGL installed')" 2>$null || Write-Host "PyKotorGL optional (requires OpenGL dependencies)" -ForegroundColor Yellow
python -c "import pykotor.font; print('✓ PyKotorFont installed')" 2>$null || Write-Host "PyKotorFont optional (requires Pillow)" -ForegroundColor Yellow

Write-Host "`nDevelopment environment setup complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "  1. Activate the virtual environment: .\$VenvName\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  2. Run tests: pytest tests/" -ForegroundColor White
Write-Host "  3. Run linter: ruff check ." -ForegroundColor White
Write-Host "  4. Check formatting: ruff format --check ." -ForegroundColor White

