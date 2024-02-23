param (
  [switch]$noprompt
)
$this_noprompt = $noprompt

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$rootPath = (Resolve-Path -LiteralPath "$scriptPath/..").Path
Write-Host "The path to the script directory is: $scriptPath"
Write-Host "The path to the root directory is: $rootPath"

Write-Host "Initializing python virtual environment..."
$this_noprompt_arg = if ($this_noprompt) {'-noprompt'} else {''}
$venv_name_arg = if ($venv_name) {"-venv_name $venv_name"} else {''}
. $rootPath/install_python_venv.ps1 $this_noprompt_arg $venv_name_arg

Write-Host "Installing required packages to build the holocron toolset..."
. $pythonExePath -m pip install --upgrade pip --prefer-binary --progress-bar on
. $pythonExePath -m pip install pyinstaller --prefer-binary --progress-bar on
. $pythonExePath -m pip install -r ($rootPath + $pathSep + "Libraries" + $pathSep + "PyKotor" + $pathSep + "requirements.txt") --prefer-binary --compile --progress-bar on -U

Write-Host "EXTRA PYTHONPATH: '$env:PYTHONPATH'"
$pyInstallerArgs = @{
    'exclude-module' = @(
        '',
        'numpy',
        'PyQt5',
        'PIL',
        'Pillow',
        'matplotlib',
        'multiprocessing',
        'PyOpenGL',
        'PyGLM',
        'dl_translate',
        'torch',
        'deep_translator',
        'deepl-cli',
        'playwright',
        'pyquery',
        'arabic-reshaper',
        'PyQt5-Qt5',
        'PyQt5-sip',
        'watchdog',
        'Markdown',
        'pyperclip',
        'setuptools',
        'wheel',
        'ruff',
        'pylint',
        'pykotor.gl',
        'pykotorgl',
        'pykotor.font',
        'pykotorfont'
        'pykotor.secure_xml',
        'mypy-extensions',
        'mypy',
        'isort',
        'install_playwright',
        'greenlet',
        'cssselect',
        'beautifulsoup4 '
    )
    'clean' = $true
    'console' = $true
    'onefile' = $true
    'noconfirm' = $true
    'name' = "GuiDuplicator"
    'distpath'=($rootPath + $pathSep + "dist")
    'upx-dir' = "C:\GitHub\upx-win32"
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
    $finalExecutablePath = "$rootPath\dist\GuiDuplicator.exe"
} elseif ((Get-OS) -eq "Linux") {
    $finalExecutablePath = "$rootPath/dist/GuiDuplicator"
} elseif ((Get-OS) -eq "Mac") {
    $finalExecutablePath = "$rootPath/dist/GuiDuplicator.app"
}

# Delete the final executable if it exists
if (Test-Path -Path $finalExecutablePath) {
    Remove-Item -Path $finalExecutablePath -Force
}

# Combine pyInstallerArgsString with pythonPathArgsString
$finalPyInstallerArgsString = "$pythonPathArgsString $pyInstallerArgsString"

$current_working_dir = (Get-Location).Path
Set-Location -LiteralPath (Resolve-Path -LiteralPath "$rootPath/Tools/GuiDuplicator/src").Path
$command = "$pythonExePath -m PyInstaller $finalPyInstallerArgsString `"__main__.py`""
Write-Host $command
Invoke-Expression $command

# Check if the final executable exists
if (-not (Test-Path -Path $finalExecutablePath)) {
    Write-Error "GUI Duplicator could not be compiled, scroll up to find out why"   
} else {
    Write-Host "GUI Duplicator was compiled to '$finalExecutablePath'"
}
Set-Location -LiteralPath $current_working_dir

if (-not $this_noprompt) {
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
