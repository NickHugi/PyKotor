param (
  [string]$venv_name=".venv",
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

$current_working_dir = (Get-Location).Path
Set-Location -LiteralPath (Resolve-Path -LiteralPath "$rootPath/Tools/HoloPatcher/src").Path

# Determine the final executable path
$finalExecutablePath = $null
if ((Get-OS) -eq "Windows") {
    $finalExecutablePath = "$rootPath\dist\HoloPatcher.exe"
} elseif ((Get-OS) -eq "Linux") {
    $finalExecutablePath = "$rootPath/dist/HoloPatcher"
} elseif ((Get-OS) -eq "Mac") {
    $finalExecutablePath = "$rootPath/dist/HoloPatcher.app"
}

# Delete the final executable if it exists
if (Test-Path -Path $finalExecutablePath) {
    Remove-Item -Path $finalExecutablePath -Force
}

Write-Host "Compiling HoloPatcher..."
$iconExtension = if ((Get-OS) -eq 'Mac') {'icns'} else {'ico'}
$pyInstallerArgs = @{
    'exclude-module' = @(
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
        'beautifulsoup4'
    )
    'clean' = $true
    'noconsole' = $true
    'onefile' = $true
    'noconfirm' = $true
    'distpath' = ($rootPath + $pathSep + "dist")
    'name' = 'HoloPatcher'
    'upx-dir' = "C:\GitHub\upx-win64"
    'icon' = "..$pathSep" + "resources$pathSep" + "icons$pathSep" + "patcher_icon_v2.$iconExtension"
}

$pyInstallerArgs = $pyInstallerArgs.GetEnumerator() | ForEach-Object {
    $key = $_.Key
    $value = $_.Value

    if ($value -is [System.Array]) {
        # Handle array values
        $arr = @()
        foreach ($elem in $value) {
            $arr += "--$key=$elem"
        }
        $arr
    } else {
        # Handle key-value pair arguments
        if ($value -eq $true) {
            "--$key"
        } elseif ($value -eq $false) {
        } else {
            "--$key=$value"
        }
    }
}

# Add PYTHONPATH paths as arguments
$env:PYTHONPATH -split ';' | ForEach-Object {
    $pyInstallerArgs += "--path=$_"
}

# Define each argument as an element in an array
$argumentsArray = @(
    "-m",
    "PyInstaller"
)
# Unpack $pyInstallerArgs into $argumentsArray
foreach ($arg in $pyInstallerArgs) {
    $argumentsArray += $arg
}

# Append the final script path
$argumentsArray += "__main__.py"

# Use the call operator with the arguments array
Write-Host "Executing command: $pythonExePath $argumentsArray"
& $pythonExePath $argumentsArray

# Check if the final executable exists
if (-not (Test-Path -Path $finalExecutablePath)) {
    Write-Error "HoloPatcher could not be compiled, scroll up to find out why"   
} else {
    Write-Host "HoloPatcher was compiled to '$finalExecutablePath'"
}
Set-Location -LiteralPath $current_working_dir

if (-not $this_noprompt) {
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}