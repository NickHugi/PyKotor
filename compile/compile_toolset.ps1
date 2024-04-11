[CmdletBinding(PositionalBinding=$false)]
param(
  [switch]$noprompt,
  [string]$venv_name = ".venv",
  [string]$upx_dir
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

$current_working_dir = (Get-Location).Path
Set-Location -LiteralPath (Resolve-Path -LiteralPath "$rootPath/Tools/HolocronToolset/src").Path

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
if (Test-Path -LiteralPath $finalExecutablePath) {
    Remove-Item -LiteralPath $finalExecutablePath -Force
}

Write-Host "Extra PYTHONPATH paths:\n'$env:PYTHONPATH'\n\n"
$iconExtension = if ((Get-OS) -eq 'Mac') {'icns'} else {'ico'}
$pyInstallerArgs = @{
    'exclude-module' = @(
        'dl_translate',
        'torch'
    )
    'upx-exclude' = @(
        '_uuid.pyd',
        'api-ms-win-crt-environment-l1-1-0.dll',
        'api-ms-win-crt-string-l1-1-0.dll',
        'api-ms-win-crt-convert-l1-1-0.dll',
        'api-ms-win-crt-heap-l1-1-0.dll',
        'api-ms-win-crt-conio-l1-1-0.dll',
        'api-ms-win-crt-filesystem-l1-1-0.dll',
        'api-ms-win-crt-stdio-l1-1-0.dll',
        'api-ms-win-crt-process-l1-1-0.dll',
        'api-ms-win-crt-locale-l1-1-0.dll',
        'api-ms-win-crt-time-l1-1-0.dll',
        'api-ms-win-crt-math-l1-1-0.dll',
        'api-ms-win-crt-runtime-l1-1-0.dll',
        'api-ms-win-crt-utility-l1-1-0.dll',
        'python3.dll',
        'api-ms-win-crt-private-l1-1-0.dll',
        'api-ms-win-core-timezone-l1-1-0.dll',
        'api-ms-win-core-file-l1-1-0.dll',
        'api-ms-win-core-processthreads-l1-1-1.dll',
        'api-ms-win-core-processenvironment-l1-1-0.dll',
        'api-ms-win-core-debug-l1-1-0.dll',
        'api-ms-win-core-localization-l1-2-0.dll',
        'api-ms-win-core-processthreads-l1-1-0.dll',
        'api-ms-win-core-errorhandling-l1-1-0.dll',
        'api-ms-win-core-handle-l1-1-0.dll',
        'api-ms-win-core-util-l1-1-0.dll',
        'api-ms-win-core-profile-l1-1-0.dll',
        'api-ms-win-core-rtlsupport-l1-1-0.dll',
        'api-ms-win-core-namedpipe-l1-1-0.dll',
        'api-ms-win-core-libraryloader-l1-1-0.dll',
        'api-ms-win-core-file-l1-2-0.dll',
        'api-ms-win-core-synch-l1-2-0.dll',
        'api-ms-win-core-sysinfo-l1-1-0.dll',
        'api-ms-win-core-console-l1-1-0.dll',
        'api-ms-win-core-string-l1-1-0.dll',
        'api-ms-win-core-memory-l1-1-0.dll',
        'api-ms-win-core-synch-l1-1-0.dll',
        'api-ms-win-core-interlocked-l1-1-0.dll',
        'api-ms-win-core-datetime-l1-1-0.dll',
        'api-ms-win-core-file-l2-1-0.dll',
        'api-ms-win-core-heap-l1-1-0.dll'
    )
    'clean' = $true
    'noconsole' = $true  # https://github.com/pyinstaller/pyinstaller/wiki/FAQ#mac-os-x  https://pyinstaller.org/en/stable/usage.html#cmdoption-w
    'onefile' = $true
    'noconfirm' = $true
    #'debug' = 'all'
    'name' = "HolocronToolset"
    'distpath'=($rootPath + $pathSep + "dist")
    'upx-dir' = $upx_dir
    'icon'="resources/icons/sith.$iconExtension"
}
switch ($qtApi) {
    "PyQt5" {
        $tempArray = $pyInstallerArgs['exclude-module']
        $tempArray += "PyQt6", "PySide2", "PySide6"
        $pyInstallerArgs['exclude-module'] = $tempArray
    }
    "PyQt6" {
        $tempArray = $pyInstallerArgs['exclude-module']
        $tempArray += "PyQt5", "PySide2", "PySide6"
        $pyInstallerArgs['exclude-module'] = $tempArray
    }
    "PySide2" {
        $tempArray = $pyInstallerArgs['exclude-module']
        $tempArray += "PyQt6", "PyQt5", "PySide6"
        $pyInstallerArgs['exclude-module'] = $tempArray
    }
    "PySide6" {
        $tempArray = $pyInstallerArgs['exclude-module']
        $tempArray += "PyQt6", "PySide2", "PyQt5"
        $pyInstallerArgs['exclude-module'] = $tempArray
    }
    default {
        throw;
    }
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
if ($env:GITHUB_ACTIONS -eq "true") {  # HACK for github runners using python 3.12
    $pyInstallerArgs += '--paths C:\Miniconda\'
}

# Append the final script path
$argumentsArray += "toolset/__main__.py"

# Use the call operator with the arguments array
Write-Host "Executing command: $pythonExePath $argumentsArray"
& $pythonExePath $argumentsArray

# Check if the final executable exists
if (-not (Test-Path -LiteralPath $finalExecutablePath)) {
    Write-Error "Holocron Toolset could not be compiled, scroll up to find out why"   
} else {
    Write-Host "Holocron Toolset was compiled to '$finalExecutablePath'"
}
Set-Location -LiteralPath $current_working_dir

if (-not $this_noprompt) {
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
