#!/usr/bin/env pwsh

[CmdletBinding(PositionalBinding=$false)]
param(
  [switch]$noprompt,
  [string]$venv_name = ".venv"
)
$this_noprompt = $noprompt

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$rootPath = (Resolve-Path -LiteralPath "$scriptPath/..").Path
Write-Host "The path to the script directory is: $scriptPath"
Write-Host "The path to the root directory is: $rootPath"

Write-Host "Initializing python virtual environment..."
if ($this_noprompt) {
    . $rootPath/install_python_venv.ps1 -noprompt -venv_name $venv_name
} else {
    . $rootPath/install_python_venv.ps1 -venv_name $venv_name
}

Write-Host "Installing required packages to build the kit generator tool..."
& $pythonExePath -m pip install --upgrade pip --prefer-binary --progress-bar on
$pythonImplementation = & $pythonExePath -c "import platform; print(platform.python_implementation())"
if ((Get-OS) -eq "Windows" -and $pythonImplementation.Trim() -eq "PyPy") {
    Write-Host "PyPy detected on Windows. Installing PyInstaller with PyPy support..."
    & $pythonExePath -m pip install "pyinstaller>=6.3.0,!=6.15.0,!=6.15.1,!=6.16.0" --prefer-binary --progress-bar on
} else {
    & $pythonExePath -m pip install pyinstaller --prefer-binary --progress-bar on
}
if ((Get-OS) -eq "Windows") {
    Write-Host "Ensuring Windows-specific build dependencies are present..."
    # PyInstaller's Windows bootloader expects pywin32-ctypes; keep it pinned even in PyPy environments.
    & $pythonExePath -m pip install pywin32-ctypes --prefer-binary --progress-bar on
    if ($pythonImplementation.Trim() -ne "PyPy") {
        # CPython builds still require pywin32 for win32api shims.
        & $pythonExePath -m pip install pywin32 --prefer-binary --progress-bar on
    }
}
& $pythonExePath -m pip install -r ($rootPath + $pathSep + "Tools" + $pathSep + "KitGenerator" + $pathSep + "requirements.txt") --prefer-binary --compile --progress-bar on -U
& $pythonExePath -m pip install -r ($rootPath + $pathSep + "Libraries" + $pathSep + "PyKotor" + $pathSep + "requirements.txt") --prefer-binary --compile --progress-bar on -U

