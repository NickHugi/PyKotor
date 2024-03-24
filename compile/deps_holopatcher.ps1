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
if ($this_noprompt) {
    . $rootPath/install_python_venv.ps1 -noprompt -venv_name $venv_name
} else {
    . $rootPath/install_python_venv.ps1 -venv_name $venv_name
}

if ((Get-OS) -eq "Mac") {
    Write-Host "path: '$pythonExePath'"
    $versionObject = Get-Python-Version $pythonExePath
    $pyVersion = "{0}.{1}" -f $versionObject.Major, $versionObject.Minor
    Write-Host "pyversion: $versionObject major/minor $pyVersion"
    brew update
    brew install python-tk@$pyVersion tcl-tk
} elseif ((Get-OS) -eq "Linux") {
    if (Test-Path -Path "/etc/os-release") {
        switch ((Get-Linux-Distro-Name)) {
            "debian" {
                sudo apt-get update
                sudo apt-get install -y tcl8.6 tk8.6 tcl8.6-dev tk8.6-dev python3-tk python3-pip
                break
            }
            "ubuntu" {
                sudo apt-get update
                sudo apt-get install -y tcl8.6 tk8.6 tcl8.6-dev tk8.6-dev python3-tk python3-pip
                break
            }
            "fedora" {
                sudo dnf install -y tk-devel tcl-devel python3-tkinter python3-pip
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

Write-Host "Installing required packages to build holopatcher..."
. $pythonExePath -m pip install --upgrade pip --prefer-binary --progress-bar on
. $pythonExePath -m pip install pyinstaller --prefer-binary --progress-bar on
. $pythonExePath -m pip install -r ($rootPath + $pathSep + "Tools" + $pathSep + "HoloPatcher" + $pathSep + "requirements.txt") --prefer-binary --progress-bar on
. $pythonExePath -m pip install -r ($rootPath + $pathSep + "Tools" + $pathSep + "HoloPatcher" + $pathSep + "recommended.txt") --prefer-binary --progress-bar on
. $pythonExePath -m pip install -r ($rootPath + $pathSep + "Libraries" + $pathSep + "PyKotor" + $pathSep + "requirements.txt") --prefer-binary --progress-bar on
