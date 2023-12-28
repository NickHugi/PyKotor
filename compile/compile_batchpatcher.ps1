
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$rootPath = (Resolve-Path -LiteralPath "$scriptPath/..").Path
Write-Host "The path to the script directory is: $scriptPath"
Write-Host "The path to the root directory is: $rootPath"

Write-Host "Initializing python virtual environment..."
. $rootPath/install_python_venv.ps1

Write-Host "Installing required packages to build the batchpatcher..."
. $pythonExePath -m pip install --upgrade pip --prefer-binary --progress-bar on
. $pythonExePath -m pip install pyinstaller --prefer-binary --progress-bar on
. $pythonExePath -m pip install -r ($rootPath + $pathSep + "Tools" + $pathSep + "BatchPatcher" + $pathSep + "requirements.txt") --prefer-binary --progress-bar on -U --upgrade-strategy "eager"
. $pythonExePath -m pip install -r ($rootPath + $pathSep + "Libraries" + $pathSep + "PyKotor" + $pathSep + "requirements.txt") --prefer-binary --progress-bar on -U --upgrade-strategy "eager"
. $pythonExePath -m pip install -r ($rootPath + $pathSep + "Libraries" + $pathSep + "PyKotorFont" + $pathSep + "requirements.txt") --prefer-binary --progress-bar on -U --upgrade-strategy "eager"

if ( (Get-OS) -eq "Linux" ) {
    . sudo apt install python3-tk -y
} elseif ( (Get-OS) -eq "Mac" ) {
    . brew install python-tk
}

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
        'pykotor-gl '
    )
    'console' = $true
    'onefile' = $true
    'noconfirm' = $true
    'name' = 'K_BatchPatcher'
    'distpath' = ($rootPath + $pathSep + 'dist')
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
    $finalExecutablePath = "$rootPath\dist\K_BatchPatcher.exe"
} elseif ((Get-OS) -eq "Linux") {
    $finalExecutablePath = "$rootPath/dist/K_BatchPatcher"
} elseif ((Get-OS) -eq "Mac") {
    $finalExecutablePath = "$rootPath/dist/K_BatchPatcher.app"
}

# Delete the final executable if it exists
if (Test-Path -Path $finalExecutablePath) {
    Remove-Item -Path $finalExecutablePath -Force
}

# Combine pyInstallerArgsString with pythonPathArgsString
$finalPyInstallerArgsString = "$pythonPathArgsString $pyInstallerArgsString"

Set-Location -LiteralPath (Resolve-Path -LiteralPath "$rootPath/Tools/BatchPatcher/src").Path
$command = "$pythonExePath -m PyInstaller $finalPyInstallerArgsString `"__main__.py`""
Write-Host $command
Invoke-Expression $command

# Check if the final executable exists
if (-not (Test-Path -Path $finalExecutablePath)) {
    Write-Error "K_BatchPatcher could not be compiled, scroll up to find out why"   
} else {
    Write-Host "K_BatchPatcher was compiled to '$finalExecutablePath'"
}
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
