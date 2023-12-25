
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$rootPath = (Resolve-Path -LiteralPath "$scriptPath/..").Path
Write-Host "The path to the script directory is: $scriptPath"
Write-Host "The path to the root directory is: $rootPath"

Write-Host "Initializing python virtual environment..."
. $rootPath/install_python_venv.ps1

Write-Host "Installing required packages to build the batchpatcher..."
. $pythonExePath -m pip install --upgrade pip
. $pythonExePath -m pip install pyinstaller --prefer-binary
. $pythonExePath -m pip install -r "$rootPath/Tools/BatchPatcher/requirements.txt" --prefer-binary
. $pythonExePath -m pip install -r "$rootPath/Libraries/PyKotor/requirements.txt" --prefer-binary
. $pythonExePath -m pip install -r "$rootPath/Libraries/PyKotorFont/requirements.txt" --prefer-binary

if ( (Get-OS) -eq "Linux" ) {
    . sudo apt install python3-tk -y
} elseif ( (Get-OS) -eq "Mac" ) {
    . brew install python-tk
}

Write-Host "EXTRA PYTHONPATH: '$env:PYTHONPATH'"
$pyInstallerArgs = @{
    'exclude-module' = @(
        '',
        'dl_translate',
        'torch'
        'PyQt5'
        'PyOpenGL'
        'PyGLM'
        'numpy'
        'multiprocessing'
    )
    "console"=$true
    "onefile"=$true
    "noconfirm"=$true
    "name"="K_BatchPatcher"
    "distpath"="$rootPath/dist"
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

# Combine pyInstallerArgsString with pythonPathArgsString
$finalPyInstallerArgsString = "$pythonPathArgsString $pyInstallerArgsString"

Set-Location -LiteralPath (Resolve-Path -LiteralPath "$rootPath/Tools/BatchPatcher/src").Path
$command = "$pythonExePath -m PyInstaller $finalPyInstallerArgsString `"__main__.py`""
Write-Host $command
Invoke-Expression $command
