param(
  [switch]$noprompt,
  [string]$venv_name = ".venv"
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

if ((Get-OS) -eq "Mac") {
    brew install python@3.12 python-tk
} elseif ((Get-OS) -eq "Linux") {
    if (Test-Path -Path "/etc/os-release") {
        switch ((Get-Linux-Distro-Name)) {
            "debian" {
                sudo apt-get update
                sudo apt-get install -y tcl8.6 tk8.6 tcl8.6-dev tk8.6-dev python3-tk
                break
            }
            "ubuntu" {
                sudo apt-get update
                sudo apt-get install -y tcl8.6 tk8.6 tcl8.6-dev tk8.6-dev python3-tk
                break
            }
            "fedora" {
                sudo dnf install -y tk-devel tcl-devel python3-tkinter
                break
            }
            "almalinux" {
                sudo yum install -y tk-devel tcl-devel python3-tkinter
                break
            }
            "rocky" {
                sudo yum install -y tk-devel tcl-devel python3-tkinter
                break
            }
            "alpine" {
                sudo apk add --update tcl tk python3-tkinter ttf-dejavu fontconfig
                break
            }
            "arch" {
                sudo pacman -Syu --noconfirm tk tcl mpdecimal
                break
            }
            "manjaro" {
                sudo pacman -Syu --noconfirm tk tcl mpdecimal
                break
            }
            "opensuse" {
                sudo zypper install -y tk-devel tcl-devel python3-tk
                break
            }
            default {
                Write-Warning "Distribution not recognized or not supported by this script."
            }
        }
    }
}

Write-Host "Installing required packages to build the batchpatcher..."
. $pythonExePath -m pip install --upgrade pip --prefer-binary --progress-bar on
. $pythonExePath -m pip install pyinstaller --prefer-binary --progress-bar on
. $pythonExePath -m pip install -r ($rootPath + $pathSep + "Tools" + $pathSep + "BatchPatcher" + $pathSep + "requirements.txt") --prefer-binary --progress-bar on
. $pythonExePath -m pip install -r ($rootPath + $pathSep + "Libraries" + $pathSep + "PyKotor" + $pathSep + "requirements.txt") --prefer-binary --progress-bar on
. $pythonExePath -m pip install -r ($rootPath + $pathSep + "Libraries" + $pathSep + "PyKotorFont" + $pathSep + "requirements.txt") --prefer-binary --progress-bar on
