[CmdletBinding(PositionalBinding=$false)]
param(
    [switch]$noprompt,
    [string]$venv_name = ".venv",
    [string]$upx_dir
)
$this_noprompt = $noprompt
$exclusive_whitelist = $true

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

# List all Python modules available in the environment
$pythonCommand = "import pkgutil; [print(m.name) for m in pkgutil.iter_modules()]"
$modulesArray = & $pythonExePath -c $pythonCommand | ForEach-Object { $_.Trim() }

# Path to the site-packages directory
$venvPath = Join-Path -Path $rootPath -ChildPath "$venv_name\Lib\site-packages"

# Define size threshold
$sizeThreshold = 1KB

# Find directories and files in site-packages matching module names, check sizes
$largeModules = @()
foreach ($moduleName in $modulesArray) {
    $modulePath = Join-Path -Path $venvPath -ChildPath $moduleName
    if (Test-Path $modulePath) {
        $dirSize = (Get-ChildItem -Path $modulePath -Recurse | Measure-Object -Property Length -Sum).Sum
        if ($dirSize -ge $sizeThreshold) {
            #Write-Output "Found large module $modulePath with size $dirSize (exceeding threshold $sizeThreshold)"
            $largeModules += $moduleName
        }
    }
}

# Whitelisted modules to keep.
$whitelistedModules = @(
    'sys', 'os', "collections", "encodings", "codecs", "io",
    "abc", "stat", "_collections_abc", "ntpath", "genericpath",
    "__future__", "contextlib", "operator", "keyword", "heapq",
    "reprlib", "functools", "types", "ctypes", "_ctypes", "inspect",
    "dis", "opcode", "enum", "importlib", "warnings", "linecache",
    "tokenize", "re", "sre_compile",
    "requests", "urllib3", "charset-normalizer", 'pykotor', 'ply',
    "charset_normalizer", "idna", "certifi", "Crypto"
)

# Exclude these large modules, don't fill excludes with an element if it's in the whitelist.
$excludeModules = @($largeModules | Where-Object { $whitelistedModules -notcontains $_ })
$excludedPaths = @(
    (Resolve-Path -LiteralPath "$rootPath\Libraries\PyKotorGL\src"),
    (Resolve-Path -LiteralPath "$rootPath\Libraries\PyKotorFont\src")
)

# Split PYTHONPATH into an array, filter out excluded paths, then rejoin
$filteredPythonPath = ($env:PYTHONPATH -split ';' | Where-Object {
    $currentPath = $_
    $isExcluded = $false
    foreach ($excludedPath in $excludedPaths) {
        if ($currentPath -like "*$excludedPath*") {
            $isExcluded = $true
            break
        }
    }
    -not $isExcluded
}) -join ';'

# Update PYTHONPATH to the filtered version
Write-Host "Old PYTHONPATH: $env:PYTHONPATH"
$env:PYTHONPATH = $filteredPythonPath
Write-Host "New PYTHONPATH: $env:PYTHONPATH"


$src_path = (Resolve-Path -LiteralPath "$rootPath/Tools/HoloPatcher/src")
$current_working_dir = (Get-Location).Path
Set-Location -LiteralPath $src_path
Write-Host "SRC_PATH: $src_path cwd: $current_working_dir"

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
if (Test-Path -LiteralPath $finalExecutablePath) {
    Remove-Item -LiteralPath $finalExecutablePath -Force
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
    #'debug' = 'imports'
    'log-level' = 'INFO'
    'clean' = $true
    'windowed' = $true  # https://github.com/pyinstaller/pyinstaller/wiki/FAQ#mac-os-x  https://pyinstaller.org/en/stable/usage.html#cmdoption-w
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
            if ($key -eq "exclude-module" -and $whitelistedModules.Contains($key)) {
                Write-Host "Not excluding whitelisted module: $elem"
                continue
            }
            $arr += "--$key=$elem"
        }
        if ($key -eq "exclude-module" -and $exclusive_whitelist -eq $true) {
            Write-Host "Handling excluded whitelist: excluding $(($excludeModules | Measure-Object).Count) more found modules"
            foreach ($elem in $excludeModules) {
                $arr += "--$key=$elem"
            }
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
