
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$rootPath = (Resolve-Path -LiteralPath "$scriptPath/../").Path
Write-Host "The path to the script directory is: $scriptPath"
Write-Host "The path to the root directory is: $rootPath"

Write-Host "Initializing python virtual environment..."
. "$rootPath/install_python_venv.ps1"

Write-Host "Installing required packages to build holopatcher..."
python -m pip install --upgrade pip
python -m pip install pyinstaller
python -m pip install -r "$rootPath/Tools/HoloPatcher/requirements.txt" --prefer-binary --no-cache-dir
python -m pip install -r "$rootPath/Libraries/PyKotor/requirements.txt" --prefer-binary --no-cache-dir

if ( $env:OS -eq "Unix" ) {
    & "sudo apt install python3-tkinter"
} elseif ( $env:OS -eq "Darwin" ) {
    & "brew install python-tk"
}

Write-Host "Compiling HoloPatcher..."
Set-Location -LiteralPath (Resolve-Path -LiteralPath "$rootPath/Tools/HoloPatcher/src").Path
python -m PyInstaller `
    --exclude-module=numpy `
    --exclude-module=PyQt5 `
    --exclude-module=PIL `
    --exclude-module=Pillow `
    --exclude-module=matplotlib `
    --exclude-module=multiprocessing `
    --exclude-module=PyOpenGL `
    --exclude-module=PyGLM `
    --exclude-module=dl_translate `
    --exclude-module=torch `
    --noconsole `
    --onefile `
    --noconfirm `
    --distpath="$rootPath/dist" `
    --name=HoloPatcher `
    --upx-dir="$env:USERPROFILE/Documents/GitHub/upx-win32" `
    --icon="../resources/icons/patcher_icon_v2.ico" `
    __main__.py