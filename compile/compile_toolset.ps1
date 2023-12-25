
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$rootPath = (Resolve-Path -LiteralPath "$scriptPath/..").Path
Write-Host "The path to the script directory is: $scriptPath"
Write-Host "The path to the root directory is: $rootPath"

Write-Host "Initializing python virtual environment..."
. $rootPath/install_python_venv.ps1

Write-Host "Installing required packages to build the holocron toolset..."
. $pythonExePath -m pip install --upgrade pip
. $pythonExePath -m pip install pyinstaller --prefer-binary
. $pythonExePath -m pip install -r "$rootPath/Tools/HolocronToolset/requirements.txt" --prefer-binary
. $pythonExePath -m pip install -r "$rootPath/Libraries/PyKotor/requirements.txt" --prefer-binary
. $pythonExePath -m pip install -r "$rootPath/Libraries/PyKotorGL/requirements.txt" --prefer-binary

if ( (Get-OS) -eq "Linux" ) {
    . sudo apt install python3-pyqt5
} elseif ( (Get-OS) -eq "Mac" ) {
    . brew install pyqt5
}

Write-Host "Compiling toolset..."
Set-Location -LiteralPath (Resolve-Path -LiteralPath "$rootPath/Tools/HolocronToolset/src").Path
. $pythonExePath -m PyInstaller `
    -m `
    PyInstaller `
    --noconsole `
    --onefile `
    --noconfirm `
    --name=HolocronToolset `
    --distpath=$rootPath/dist `
    --exclude-module=dl_translate `
    --exclude-module=torch `
    --icon=resources/icons/sith.ico `
    --upx-dir="$env:USERPROFILE/Documents/GitHub/upx-win32" `
    toolset/__main__.py
