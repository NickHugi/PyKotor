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
. $rootPath/install_python_venv.ps1

# Execute the Python code using the specified interpreter
try {
    & $pythonExePath -c "import tkinter; print('Tkinter is available')"
    Write-Host "Tkinter is available for $($pythonExePath)"
} catch {
    Write-Host "Tkinter is not available for $($pythonExePath)"
    $venvPath = ""
    if ($null -ne $env:VIRTUAL_ENV) {
        Write-Host "A virtual environment is activated."
        Write-Host "Virtual Environment Root: $($env:VIRTUAL_ENV)"
        $venvPath = $env:VIRTUAL_ENV
        deactivate
    } else {
        Write-Host "No virtual environment is activated."
    }
    if ((Get-OS) -eq "Mac") {
        brew install python-tk
    } elseif ((Get-OS) -eq "Linux") {
        if (Test-Path -Path "/etc/os-release") {
            $distro = (Get-Linux-Distro-Name)
            $command = ""
            switch ($distro) {
                "debian" {
                    $command = "sudo apt-get install python3-tk -y"
                    break
                }
                "ubuntu" {
                    $command = "sudo apt-get install python3-tk -y"
                    break
                }
                "fedora" {
                    $command = "sudo dnf install python3-tkinter python3.10-tkinter"
                    break
                }
                "almalinux" {
                    sudo dnf install tk-devel tcl-devel
                    $command = "sudo dnf install python3-tkinter -y"
                    break
                }
                "alpine" {
                    $command = "sudo apk add ttf-dejavu fontconfig python3-tkinter"
                    break
                }
                "arch" {
                    $command = "sudo pacman -Sy tk mpdecimal --noconfirm"
                }
            }
        
            if ($command -eq "") {
                Write-Warning "Dist '$distro' not supported for automated system package install, please install the dependencies if you experience problems."
            } else {
                Write-Host "Executing command: $command"
                Invoke-Expression $command
            }
        }
    }
    if ($venvPath -ne "" -and $null -ne $venvPath) {
        Write-Host "Deleting old venv at '$venvPath'..."
        Remove-Item -Path $venvPath -Recurse -Force
    }
    Write-Host "Reinitializing python virtual environment..."
    $this_noprompt_arg = if ($this_noprompt) {'-noprompt'} else {''}
    $venv_name_arg = if ($venv_name) {"-venv_name $venv_name"} else {''}
    . $rootPath/install_python_venv.ps1 $this_noprompt_arg $venv_name_arg
}

Write-Host "Installing required packages to build the batchpatcher..."
. $pythonExePath -m pip install --upgrade pip --prefer-binary --progress-bar on
. $pythonExePath -m pip install pyinstaller --prefer-binary --progress-bar on
. $pythonExePath -m pip install -r ($rootPath + $pathSep + "Tools" + $pathSep + "BatchPatcher" + $pathSep + "requirements.txt") --prefer-binary --progress-bar on
. $pythonExePath -m pip install -r ($rootPath + $pathSep + "Libraries" + $pathSep + "PyKotor" + $pathSep + "requirements.txt") --prefer-binary --progress-bar on
. $pythonExePath -m pip install -r ($rootPath + $pathSep + "Libraries" + $pathSep + "PyKotorFont" + $pathSep + "requirements.txt") --prefer-binary --progress-bar on


$current_working_dir = (Get-Location).Path
Set-Location -LiteralPath (Resolve-Path -LiteralPath "$rootPath/Tools/BatchPatcher/src").Path

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

Write-Host "Compiling BatchPatcher..."
$pyInstallerArgs = @{
    'exclude-module' = @(
        ''
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

$pyInstallerArgs = $pyInstallerArgs.GetEnumerator() | ForEach-Object {
    $key = $_.Key
    $value = $_.Value

    if ($value -is [System.Array]) {
        # Handle array values
        $value -join "--$key="
        $value = "--$key=$value"
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
    Write-Error "BatchPatcher could not be compiled, scroll up to find out why"   
} else {
    Write-Host "BatchPatcher was compiled to '$finalExecutablePath'"
}
Set-Location -LiteralPath $current_working_dir

if (-not $this_noprompt) {
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}