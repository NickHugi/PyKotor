#!/usr/bin/env pwsh

[CmdletBinding(PositionalBinding=$false)]
param(
  [switch]$noprompt,
  [string]$venv_name = ".venv",
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


Write-Verbose "EXTRA PYTHONPATH: '$env:PYTHONPATH'"
$pyInstallerArgs = @{
    'exclude-module' = @(
        'numpy',
        'PyQt5',
        'PIL',
        'Pillow',
        'matplotlib',
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
    'console' = $true  # https://github.com/pyinstaller/pyinstaller/wiki/FAQ#mac-os-x  https://pyinstaller.org/en/stable/usage.html#cmdoption-w
    'onefile' = $true
    'noconfirm' = $true
    'name' = "KotorDiff"
    'distpath' = ($rootPath + $pathSep + 'dist')
    'upx-dir' = $upx_dir
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
if (Get-OS -eq "Windows") { $extension = "exe" } elseif ($os -eq "Linux") { $extension = "" } elseif ($os -eq "Mac") { $extension = "app" }
$finalExecutablePath = $pyInstallerArgs.distpath + $pathSep + "$($pyInstallerArgs.name).$extension"
if (Test-Path -LiteralPath $finalExecutablePath -ErrorAction SilentlyContinue) {
    Write-Host "Removing old exe at '$finalExecutablePath'"
    Remove-Item -LiteralPath $finalExecutablePath -Force
} else {
    $finalExecutablePath = "$($pyInstallerArgs.distpath)$($pathSep)$($pyInstallerArgs.name)$($pathSep)$($pyInstallerArgs.name).$extension"
    $finalExecutableDir = "$($pyInstallerArgs.distpath)$pathSep$($pyInstallerArgs.name)"
    if (Test-Path -LiteralPath $finalExecutableDir -ErrorAction SilentlyContinue) {
        Write-Host "Removing old dist dir at '$finalExecutableDir'"
        Remove-Item -LiteralPath $finalExecutableDir -Recurse -Force
    }
}
if ($clean -and (Test-Path $pyInstallerArgs.workpath -ErrorAction SilentlyContinue)) { Remove-Item -LiteralPath $pyInstallerArgs.workpath -Recurse -Force }


Write-Host "Compiling $($pyInstallerArgs.name)..."
Push-Location -LiteralPath $toolSrcDir
try {
    $argumentsArray = @('-m', 'PyInstaller') + $argumentsArray + "$($pyInstallerArgs.name)$pathSep`__main__.py"
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


# Append the final script path
$argumentsArray += "kotordiff/__main__.py"
Write-Host "Installing required packages to build the kotordiff tool..."
& $pythonExePath -m pip install --upgrade pip --prefer-binary --progress-bar on
& $pythonExePath -m pip install pyinstaller --prefer-binary --progress-bar on
& $pythonExePath -m pip install -r ($rootPath + $pathSep + "Libraries" + $pathSep + "PyKotor" + $pathSep + "requirements.txt") --prefer-binary --compile --progress-bar on -U

Write-Host "Compiling KotorDiff..."

# Use the call operator with the arguments array
Write-Host "Executing command: $pythonExePath $argumentsArray"
& $pythonExePath $argumentsArray

# Check if the final executable exists
if (-not (Test-Path -LiteralPath $finalExecutablePath)) {
    Write-Error "KotorDiff could not be compiled, scroll up to find out why"   
} else {
    Write-Host "KotorDiff was compiled to '$finalExecutablePath'"
}
Set-Location -LiteralPath $current_working_dir

if (-not $this_noprompt) {
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
