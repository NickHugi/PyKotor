#!/usr/bin/env pwsh

[CmdletBinding(PositionalBinding=$false)]
param(
    [switch]$noprompt,
    [string]$venv_name = ".venv",
    [string]$force_python_version,
    [string]$upx_dir
)
$this_noprompt = $noprompt

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$repoRootPath = (Resolve-Path -LiteralPath "$scriptPath/..").Path
Write-Host "The path to the script directory is: $scriptPath"
Write-Host "The path to the root directory is: $repoRootPath"

Write-Host "Initializing python virtual environment..."
if ($this_noprompt) {
    . $repoRootPath/install_python_venv.ps1 -noprompt -venv_name $venv_name
} else {
    . $repoRootPath/install_python_venv.ps1 -venv_name $venv_name
}
Write-Host "----------------------------------------"

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
    'distpath'=($repoRootPath + $pathSep + "dist")
    'upx-dir' = $upx_dir
    'icon'="resources/icons/sith.$iconExtension"
    'path'=''
}

$toolSrcDir = (Resolve-Path -LiteralPath "$($repoRootPath)$($pathSep)Tools$($pathSep)$($pyInstallerArgs.name)$($pathSep)src").Path
$pyInstallerArgs.workpath = "$toolSrcDir$($pathSep)build"
$pyInstallerArgs.path += $toolSrcDir
Write-Host "toolSrcDir: '$toolSrcDir'"


# Build flat arguments array.
$argumentsArray = $pyInstallerArgs.GetEnumerator() | ForEach-Object {
    if ($_.Value -is [System.Array]) {
        $arr = @()
        foreach ($elem in $($_.Value)) { $arr += "--$($_.Key)=$elem" }
        $arr
    } else {
        if ($_.Value -eq $true) { "--$($_.Key)" }
        elseif ($_.Value -eq $false) {}
        else { "--$($_.Key)=$($_.Value)" }
    }
}


# Remove old compile/build files/folders if clean is set.
if (Get-OS -eq "Windows") { $extension = "exe" } elseif (Get-OS -eq "Linux") { $extension = "" } elseif (Get-OS -eq "Mac") { $extension = "app" }
$finalExecutablePath = $pyInstallerArgs.distpath + $pathSep + "$($pyInstallerArgs.name).$extension"
if (Test-Path -LiteralPath $finalExecutablePath -ErrorAction SilentlyContinue) {
    Write-Host "Removing old exe at '$finalExecutablePath'"
    Remove-Item -LiteralPath $finalExecutablePath -Force
} else {
    $finalExecutableDir = "$($pyInstallerArgs.distpath)$pathSep$($pyInstallerArgs.name)"
    if (Test-Path $finalExecutableDir -ErrorAction SilentlyContinue) {
        $finalExecutablePath = "$($pyInstallerArgs.distpath)$($pathSep)$($pyInstallerArgs.name)$($pathSep)$($pyInstallerArgs.name).$extension"
        Write-Host "Final executable dir: $finalExecutableDir"
        if (Test-Path -LiteralPath $finalExecutableDir -ErrorAction SilentlyContinue) {
            Write-Host "Removing old dist dir at '$finalExecutableDir'"
            Remove-Item -LiteralPath $finalExecutableDir -Recurse -Force
        }
    }
}
Write-Host "Final executable path: $finalExecutablePath"
if ($pyInstallerArgs.clean -and (Test-Path $pyInstallerArgs.workpath -ErrorAction SilentlyContinue)) { Remove-Item -LiteralPath $pyInstallerArgs.workpath -Recurse -Force }


# setup QT_API env var (for pyinstaller)
if (-not $env:QT_API) {
    $env:QT_API = "PyQt5"  # Default to PyQt5 if QT_API is not set
}
switch ($env:QT_API) {
    { $_ -in "PyQt5", "PyQt6", "PySide2", "PySide6", "pyqt5", "pyqt6", "pyside2", "pyside6", "default" } {
        # Define a dictionary for mapping lowercase to correct case
        $apiMapping = @{
            "pyqt5" = "PyQt5";
            "pyqt6" = "PyQt6";
            "pyside2" = "PySide2";
            "pyside6" = "PySide6"
        }

        # Normalize $env:QT_API based on the dictionary
        if ($apiMapping.ContainsKey($env:QT_API.ToLower())) {
            $env:QT_API = $apiMapping[$env:QT_API.ToLower()]
            Write-Host "converted QT_API to '$env:QT_API'"
        } else {
            Write-Error "Invalid QT_API: '$env:QT_API', hopefully pyinstaller figures it out..."
        }

        # Default modules to exclude
        $modulesToExclude = @("PyQt5", "PyQt6", "PySide2", "PySide6") | Where-Object { $_ -ne $env:QT_API }

        # Add modules to the exclude list
        $tempArray = $pyInstallerArgs['exclude-module'] + $modulesToExclude
        $tempArrayString = $tempArray -join ", "
        Write-Host "Excluding: $tempArrayString"
        $pyInstallerArgs['exclude-module'] = $tempArray
    }
}
Write-Host "QT_API: $env:QT_API"


Write-Host "Compiling $($pyInstallerArgs.name)..."
Push-Location -LiteralPath $toolSrcDir
try {
    $argumentsArray = @('-m', 'PyInstaller') + $argumentsArray + "toolset$pathSep`__main__.py"
    Write-Host "Executing command: $pythonExePath $argumentsArray"
    & $pythonExePath $argumentsArray
} finally {
    Pop-Location
}

Write-Host "Checking '$finalExecutablePath' to see if it was built and the file exists."
if (-not (Test-Path -LiteralPath $finalExecutablePath -ErrorAction SilentlyContinue)) {
    Write-Error "$($pyInstallerArgs.name) could not be compiled, scroll up to find out why"
} else {
    Write-Host "$($pyInstallerArgs.name) was compiled to '$finalExecutablePath'"
}