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

Write-Host "Installing required packages to build hoodinstaller..."
. $pythonExePath -m pip install --upgrade pip --prefer-binary --progress-bar on
. $pythonExePath -m pip install pyinstaller --prefer-binary --progress-bar on
. $pythonExePath -m pip install -r ($rootPath + $pathSep + "Tools" + $pathSep + "HoloPatcher" + $pathSep + "requirements.txt") --prefer-binary --progress-bar on -U
. $pythonExePath -m pip install -r ($rootPath + $pathSep + "Tools" + $pathSep + "HoloPatcher" + $pathSep + "recommended.txt") --prefer-binary --progress-bar on -U
. $pythonExePath -m pip install -r ($rootPath + $pathSep + "Libraries" + $pathSep + "PyKotor" + $pathSep + "requirements.txt") --prefer-binary --progress-bar on -U

if ( (Get-OS) -eq "Linux" ) {
    . sudo apt install python3-tk -y
} elseif ( (Get-OS) -eq "Mac" ) {
    . brew install python-tk
}

Write-Host "Compiling HoodInstaller..."
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
    'noconsole' = $true
    'onefile' = $true
    'noconfirm' = $true
    'distpath' = ($rootPath + $pathSep + "dist")
    'name' = 'HoodInstaller'
    'upx-dir' = "C:\GitHub\upx-win32"
    'icon' = "..$pathSep" + "resources$pathSep" + "icons$pathSep" + "patcher_icon_v2.ico"
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
        } elseif ($value -eq $false) {
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
    $finalExecutablePath = "$rootPath\dist\HoodInstaller.exe"
} elseif ((Get-OS) -eq "Linux") {
    $finalExecutablePath = "$rootPath/dist/HoodInstaller"
} elseif ((Get-OS) -eq "Mac") {
    $finalExecutablePath = "$rootPath/dist/HoodInstaller.app"
}

# Delete the final executable if it exists
if (Test-Path -Path $finalExecutablePath) {
    Remove-Item -Path $finalExecutablePath -Recurse -Force
}

# Combine pyInstallerArgsString with pythonPathArgsString
$finalPyInstallerArgsString = "$pythonPathArgsString $pyInstallerArgsString"

$current_working_dir = (Get-Location).Path
Set-Location -LiteralPath (Resolve-Path -LiteralPath "$rootPath/Tools/HoodInstaller/src").Path
$command = "$pythonExePath -m PyInstaller $finalPyInstallerArgsString `"__main__.py`""
Write-Host $command
Invoke-Expression $command

# Check if the final executable exists
if (-not (Test-Path -Path $finalExecutablePath)) {
    Write-Error "HoodInstaller could not be compiled, scroll up to find out why"   
} else {
    Write-Host "HoodInstaller was compiled to '$finalExecutablePath'"
}
Set-Location -LiteralPath $current_working_dir

if (-not $this_noprompt) {
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}