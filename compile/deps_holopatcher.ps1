param(
  [switch]$noprompt = $false,
  [string]$venv_name = ".venv"
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

$output = & $pythonExePath -c "import tkinter; print('Tkinter is available')" 2>&1
if ($output -match "ModuleNotFoundError" -or $output -is [System.Management.Automation.ErrorRecord]) {
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
        brew install python@3.12 python-tk
    } elseif ((Get-OS) -eq "Linux") {
        if (Test-Path -Path "/etc/os-release") {
            switch ((Get-Linux-Distro-Name)) {
                "debian" {
                    sudo apt-get install python3-tk -y
                    break
                }
                "ubuntu" {
                    sudo apt-get install python3-tk -y
                    break
                }
                "fedora" {
                    sudo dnf install python3-tkinter python3.10-tkinter
                    break
                }
                "almalinux" {
                    sudo dnf install tk-devel tcl-devel
                    sudo dnf install python3-tkinter -y
                    break
                }
                "alpine" {
                    sudo apk add ttf-dejavu fontconfig python3-tkinter
                    break
                }
                "arch" {
                    sudo pacman -Syu
                    sudo pacman -Sy tk mpdecimal --noconfirm
                }
            }
        }
    }
    if ($venvPath -ne "" -and $null -ne $venvPath) {
        Write-Host "Deleting old venv at '$venvPath'..."
        Remove-Item -Path $venvPath -Recurse -Force
    }
    Write-Host "Reinitializing python virtual environment..."
    . $rootPath/install_python_venv.ps1 $this_noprompt_arg $venv_name_arg
} else {
    Write-Host "Tkinter is available for $($pythonExePath)"
}

Write-Host "Installing required packages to build holopatcher..."
. $pythonExePath -m pip install --upgrade pip --prefer-binary --progress-bar on
. $pythonExePath -m pip install pyinstaller --prefer-binary --progress-bar on
. $pythonExePath -m pip install -r ($rootPath + $pathSep + "Tools" + $pathSep + "HoloPatcher" + $pathSep + "requirements.txt") --prefer-binary --progress-bar on
. $pythonExePath -m pip install -r ($rootPath + $pathSep + "Tools" + $pathSep + "HoloPatcher" + $pathSep + "recommended.txt") --prefer-binary --progress-bar on
. $pythonExePath -m pip install -r ($rootPath + $pathSep + "Libraries" + $pathSep + "PyKotor" + $pathSep + "requirements.txt") --prefer-binary --progress-bar on
