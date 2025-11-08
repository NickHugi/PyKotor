#!/usr/bin/env pwsh

[CmdletBinding(PositionalBinding=$false)]
param(
  [switch]$noprompt,
  [string]$venv_name = ".venv",
  [string]$upx_dir
)
$ErrorActionPreference = "Stop"

$repoRootPath = (Resolve-Path -LiteralPath "$($MyInvocation.MyCommand.Definition)/../..").Path  # Path to PyKotor repo root.
Write-Host "Initializing the Python virtual environment..."
if ($noprompt) {
    . $repoRootPath/install_python_venv.ps1 -noprompt -venv_name $venv_name
} else {
    . $repoRootPath/install_python_venv.ps1 -venv_name $venv_name
}

$iconExtension = if ((Get-OS) -eq 'Mac') {'icns'} else {'ico'}
$pyInstallerArgs = @{
    'exclude-module' = @(  # add some giant packages that should never be included
        'PyQt5',
        'PyOpenGL',
        'PyGLM',
        'dl_translate',
        'torch',
        'deep_translator',
        'cefpython3'
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
    'debug' = 'imports'
    'log-level' = 'INFO'
    'clean' = $true
    'windowed' = $false  # https://github.com/pyinstaller/pyinstaller/wiki/FAQ#mac-os-x  https://pyinstaller.org/en/stable/usage.html#cmdoption-w
    'onefile' = $true
    'noconfirm' = $true
    'distpath' = "$repoRootPath$($pathSep)dist"
    #'workpath' = ""  # defined after this constructor.
    'name' = 'HoloPatcher'
    'upx-dir' = $upx_dir
    'icon' = ""  # defined after this constructor.
    'path' = $env:PYTHONPATH -split ';'
}

$toolSrcDir = (Resolve-Path -LiteralPath "$($repoRootPath)$($pathSep)Tools$($pathSep)$($pyInstallerArgs.name)$($pathSep)src").Path
$pyInstallerArgs.workpath = "$toolSrcDir$($pathSep)build"
$pyInstallerArgs.path += $toolSrcDir
$pyInstallerArgs.icon = "$toolSrcDir${pathSep}resources${pathSep}icons${pathSep}patcher_icon_v2.${iconExtension}"
Write-Host "toolSrcDir: '$toolSrcDir'"

# Remove old compile/build files/folders if clean is set.
if (Get-OS -eq "Windows") { $extension = "exe" } elseif (Get-OS -eq "Linux") { $extension = "" } elseif (Get-OS -eq "Mac") { $extension = "app" }
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
