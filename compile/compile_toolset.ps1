param (
  [switch]$noprompt
)
$this_noprompt = $noprompt

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$rootPath = (Resolve-Path -LiteralPath "$scriptPath/..").Path
Write-Host "The path to the script directory is: $scriptPath"
Write-Host "The path to the root directory is: $rootPath"

Write-Host "Initializing python virtual environment..."
. $rootPath/install_python_venv.ps1

Write-Host "Installing required packages to build the holocron toolset..."
. $pythonExePath -m pip install --upgrade pip --prefer-binary --progress-bar on
. $pythonExePath -m pip install pyinstaller --prefer-binary --progress-bar on
. $pythonExePath -m pip install -r ($rootPath + $pathSep + "Tools" + $pathSep + "HolocronToolset" + $pathSep + "requirements.txt") --prefer-binary --compile --progress-bar on -U
. $pythonExePath -m pip install -r ($rootPath + $pathSep + "Libraries" + $pathSep + "PyKotor" + $pathSep + "requirements.txt") --prefer-binary --compile --progress-bar on -U
. $pythonExePath -m pip install -r ($rootPath + $pathSep + "Libraries" + $pathSep + "PyKotorGL" + $pathSep + "requirements.txt") --prefer-binary --compile --progress-bar on -U

if ( (Get-OS) -eq "Linux" ) {
    . sudo apt install python3-pyqt5 -y
} elseif ( (Get-OS) -eq "Mac" ) {
    . brew install pyqt5
}

Write-Host "EXTRA PYTHONPATH: '$env:PYTHONPATH'"
$pyInstallerArgs = @{
    'exclude-module' = @(
        '',
        'dl_translate',
        'torch '
    )
    'clean' = $true
    'noconsole' = $true
    'onefile' = $true
    'noconfirm' = $true
    'name' = "HolocronToolset"
    'distpath'=($rootPath + $pathSep + "dist")
#    'upx-dir' = "$env:USERPROFILE\Documents\GitHub\upx-win32"
    'icon'="resources/icons/sith.ico"
}
$pyInstallerArgsString = ($pyInstallerArgs.GetEnumerator() | ForEach-Object {
    $key = $_.Key
    $value = $_.Value

    if ($value -is [System.Array]) {
        # Handle array values
        $value -join " --$key="
        $value = " --$key=$value "
    } else {
        # Handle key-value pair arguments
        if ($value -eq $true) {
            "--$key "
        } else {
            "--$key=$value "
        }
    }
}) -join ''

# Format PYTHONPATH paths and add them to the pyInstallerArgsString
$pythonPaths = $env:PYTHONPATH -split ';'
$pythonPathArgs = $pythonPaths | ForEach-Object { "--path=$_" }
$pythonPathArgsString = $pythonPathArgs -join ' '

# Determine the final executable path
$finalExecutablePath = $null
if ((Get-OS) -eq "Windows") {
    $finalExecutablePath = "$rootPath\dist\HolocronToolset.exe"
} elseif ((Get-OS) -eq "Linux") {
    $finalExecutablePath = "$rootPath/dist/HolocronToolset"
} elseif ((Get-OS) -eq "Mac") {
    $finalExecutablePath = "$rootPath/dist/HolocronToolset.app"
}

# Delete the final executable if it exists
if (Test-Path -Path $finalExecutablePath) {
    Remove-Item -Path $finalExecutablePath -Force
}

# Combine pyInstallerArgsString with pythonPathArgsString
$finalPyInstallerArgsString = "$pythonPathArgsString $pyInstallerArgsString"

$current_working_dir = (Get-Location).Path
Set-Location -LiteralPath (Resolve-Path -LiteralPath "$rootPath/Tools/HolocronToolset/src").Path
$command = "$pythonExePath -m PyInstaller $finalPyInstallerArgsString `"toolset/__main__.py`""
Write-Host $command
Invoke-Expression $command

# Check if the final executable exists
if (-not (Test-Path -Path $finalExecutablePath)) {
    Write-Error "Holocron Toolset could not be compiled, scroll up to find out why"   
} else {
    Write-Host "Holocron Toolset was compiled to '$finalExecutablePath'"
}
Set-Location -LiteralPath $current_working_dir

if (-not $this_noprompt) {
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
