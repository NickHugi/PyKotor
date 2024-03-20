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
Write-Host "Initializing python virtual environment..."
if ($this_noprompt) {
    . $rootPath/install_python_venv.ps1 -noprompt -venv_name $venv_name
} else {
    . $rootPath/install_python_venv.ps1 -venv_name $venv_name
}

$src_path = (Resolve-Path -LiteralPath "$rootPath/Tools/HoloPatcher/src")
$current_working_dir = (Get-Location).Path
Set-Location -LiteralPath $src_path

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
        'sip',
        'PyQt5-tools'
        'qt5-applications'
        'watchdog',
        'Markdown',
        'pyperclip',
        'setuptools',
        'java',
        'java.lang',
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
    'noconsole' = $true  # https://github.com/pyinstaller/pyinstaller/wiki/FAQ#mac-os-x  https://pyinstaller.org/en/stable/usage.html#cmdoption-w
    'onefile' = $true
    'noconfirm' = $true
    'distpath' = ($rootPath + $pathSep + "dist")
    'name' = 'HoloPatcher'
    'upx-dir' = $upx_dir
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

$tclTkPath = $null
if ((Get-OS) -eq "Mac") {
    try {
        $tclTkPath = $(brew --prefix tcl-tk)
        Write-Output "tcl/tk path: $tclTkPath"
    } catch {
        Write-Warning "Unable to determine Tcl/Tk path using Homebrew"
    }
}

# Prepare the Python command as a single string
$pythonCommand = @"
import tkinter
root = tkinter.Tk()
print(root.tk.exprstring('$tcl_library'))
print(root.tk.exprstring('$tk_library'))
"@
if ((Get-OS) -eq "Mac") {
    
    # Execute the Python command and capture the output
    $output = & $pythonExePath -c $pythonCommand
    
    # The output will contain both paths, one per line. Split them.
    $lines = $output -split "`n"
    
    # Assuming the first line is the Tcl library path and the second line is the Tk library path
    $tcl_library = $lines[0]
    $tk_library = $lines[1]
    
    # Output the variables to verify
    Write-Host "Raw output: $output"
    Write-Host "Tcl library path: $tcl_library"
    Write-Host "Tk library path: $tk_library"
    
    Write-Host "TCL_LIBRARY current env: '$Env:TCL_LIBRARY'"
    Write-Host "TK_LIBRARY current env: '$Env:TK_LIBRARY'"
    
    #$Env:TCL_LIBRARY = $tcl_library
    #$Env:TK_LIBRARY = $tk_library
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
if (-not (Test-Path -LiteralPath $finalExecutablePath)) {
    Write-Error "HoloPatcher could not be compiled, scroll up to find out why"   
} else {
    Write-Host "HoloPatcher was compiled to '$finalExecutablePath'"
}
Set-Location -LiteralPath $current_working_dir

if (-not $this_noprompt) {
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}