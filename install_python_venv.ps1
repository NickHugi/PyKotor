[CmdletBinding(PositionalBinding=$false)]
param(
  [switch]$noprompt,
  [string]$venv_name = ".venv"
)

$repoRootPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
function Get-OS {
    if ($IsWindows) {
        return "Windows"
    } elseif ($IsMacOS) {
        return "Mac"
    } elseif ($IsLinux) {
        return "Linux"
    }
    $os = (Get-WmiObject -Class Win32_OperatingSystem).Caption
    if ($os -match "Windows") {
        return "Windows"
    } elseif ($os -match "Mac") {
        return "Mac"
    } elseif ($os -match "Linux") {
        return "Linux"
    } else {
        Write-Error "Unknown Operating System"
        Write-Host "Press any key to exit..."
        if (-not $noprompt) {
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        }
        exit
    }
}

$pathSep = "/"
if ((Get-OS) -eq "Windows") {
    $pathSep = "\"
} else {
    # LD_LIBRARY_PATH must be set on unix systems in order to build python.
    $ldLibraryPath = [System.Environment]::GetEnvironmentVariable('LD_LIBRARY_PATH', 'Process')
    if ([string]::IsNullOrEmpty($ldLibraryPath)) {
        Write-Warning "LD_LIBRARY_PATH not defined, creating it with /usr/local/lib ..."
        [System.Environment]::SetEnvironmentVariable('LD_LIBRARY_PATH', '/usr/local/lib', 'Process')
    } elseif (-not $ldLibraryPath.Contains('/usr/local/lib')) {
        Write-Warning "LD_LIBRARY_PATH defined but no definition for /usr/local/lib, adding it now..."
        $newLdLibraryPath = $ldLibraryPath + ':/usr/local/lib'
        [System.Environment]::SetEnvironmentVariable('LD_LIBRARY_PATH', $newLdLibraryPath, 'Process')
    }
}

# Ensure script is running with elevated permissions
If ((Get-OS) -eq "Windows" -and -NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Warning "Please run PowerShell with administrator rights!"
    #Break
}

# Function to parse and set environment variables from .env file
function Set-EnvironmentVariablesFromEnvFile {
    Param (
        [string]$envFilePath
    )
    if (Test-Path $envFilePath) {
        Get-Content $envFilePath | ForEach-Object {
            if ($_ -match '^\s*(\w+)\s*=\s*(?:"(.*?)"|''(.*?)''|(.*?))\s*$') {
                $key, $value = $matches[1], $matches[2] + $matches[3] + $matches[4]
                
                Write-Debug "Processing variable: $key"
                Write-Debug "Retrieved from regex - Key: $key, Value: $value"

                # Replace ${env:VARIABLE} with actual environment variable value
                $originalValue = $value
                $value = $value -replace '\$\{env:(.*?)\}', {
                    $envVarName = $matches[1]
                    $retrievedEnvValue = [System.Environment]::GetEnvironmentVariable($envVarName, [System.EnvironmentVariableTarget]::Process)
                    # If the environment variable isn't set, use an empty string instead
                    if ($null -eq $retrievedEnvValue) {
                        $retrievedEnvValue = ""
                    }
                    Write-Debug "Replacing $envVarName '${env:$envVarName}' with '$retrievedEnvValue'"
                    return $retrievedEnvValue
                }
                
                # Split paths, trim whitespace, and remove duplicates
                $uniquePaths = @{}
                ($value -split ';').ForEach({
                    $trimmedPath = $_.Trim()
                    if (-not [string]::IsNullOrWhiteSpace($trimmedPath)) {
                        Write-Debug "Trimmed Path: $trimmedPath"
                        $absolutePath = "$repoRootPath/$trimmedPath"
                        if ( Test-Path $absolutePath -ErrorAction SilentlyContinue )
                        {
                            $resolvedPath = (Resolve-Path -LiteralPath $absolutePath).Path
                            if ($null -ne $resolvedPath) {
                                $uniquePaths[$resolvedPath] = $true
                            }
                        }
                    }
                })
                $value = ($uniquePaths.Keys -join ';')

                Write-Debug "Original value: $originalValue, Final value: $value"

                # Set environment variable
                Write-Host "Set environment variable $key from '${$env:$key}' to '$value'"
                Set-Item -Path "env:$key" -Value $value
            }
        }
        Write-Host "Environment variables set from .env file."
        return $true
    }

    # environment file not found.
    return $false
}

function Get-Linux-Distro-Name {
    if (Test-Path "/etc/os-release" -ErrorAction SilentlyContinue) {
        $osInfo = Get-Content "/etc/os-release" -Raw
        if ($osInfo -match '\nID="?([^"\n]*)"?') {
            $distroName = $Matches[1].Trim('"')
            if ($distroName -eq "ol") {
                sudo yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
                return "oracle"
            }
            return $distroName
        }
    }
    return $null
}

function Get-Linux-Distro-Version {
    $osInfo = Get-Content "/etc/os-release" -Raw
    if (Test-Path "/etc/os-release" -ErrorAction SilentlyContinue) {
        if ($osInfo -match '\nVERSION_ID="?([^"\n]*)"?') {
            $distroVersion = $Matches[1].Trim('"')
            return $distroVersion
        }
    }
    return $null
}

function Install-Linux-Deps {
    if (Test-Path "/etc/os-release") {
        $distro = (Get-Linux-Distro-Name)
        $versionId = (Get-Linux-Distro-Version)
        
        try {
            switch ($distro) {
                "debian" {
                    sudo apt-get update
                    sudo apt-get install python3 -y
                    sudo apt-get install python3-dev -y
                    sudo apt-get install python3-venv -y
                    sudo apt-get install python3-pip -y
                    break
                }
                "ubuntu" {
                    sudo apt-get update
                    sudo apt-get install python3 -y
                    sudo apt-get install python3-dev -y
                    sudo apt-get install python3-venv -y
                    sudo apt-get install python3-pip -y
                    break
                }
                "alpine" {
                    sudo apk update
                    sudo apk add --update --no-cache python3
                    ln -sf python3 /usr/bin/python
                    python3 -m ensurepip
                    pip3 install --no-cache --upgrade pip setuptools
                    break
                }
                "almalinux" {
                    sudo dnf update -y
                    #sudo dnf upgrade -y
                    #sudo dnf install python38 -y  # Won't work because the main binary doesn't contain tkinter.
                    Find-Python -intrnal
                    if ( $global:pythonInstallPath -eq "") {
                        sudo dnf install tk-devel tcl-devel -y
                        sudo dnf install openssl-devel bzip2-devel libffi-devel wget -y
                        sudo dnf groupinstall "Development Tools" -y
                        gcc --version
                        Python-Install-Unix-Source
                    }
                    python3.8 --version
                }
                "fedora" {
                    sudo dnf update -y
                    sudo dnf install python3 -y
                    sudo dnf install python3-pip -y
                    sudo dnf install git -y
                    break
                }
                "centos" {
                    sudo yum update
                    if ( $versionId -eq "7" ) {
                        sudo yum install epel-release -y
                    }
                    sudo yum install python3 -y
                    sudo yum install python3-pip -y
                    sudo yum install python3-venv -y
                    break
                }
                "arch" {
                    sudo pacman -Syu --noconfirm
                    sudo pacman -Sy base-devel wget --noconfirm
                    sudo pacman -Sy python-pip --noconfirm
                    sudo pacman -Sy python --noconfirm                    
                }
                default {
                    Write-Error "Unsupported Linux distribution for package manager install of Python."
                }
            }
            Find-Python -intrnal
            if ( $global:pythonInstallPath -eq "" ) {
                throw "Python not found/installed"
            }
        } catch {
            $userInput = Read-Host "Could not install python from your package manager, would you like to attempt to build from source instead? (y/N)"
            if ( $userInput -ne "Y" -and $userInput -ne "y" ) {
                Write-Host "Press any key to exit..."
                $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
                exit 1
            }
            # Fallback mechanism for each distribution
            switch ($distro) {
                "debian" {
                    sudo apt-get update
                    sudo apt-get install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev libbz2-dev tk-dev -y
                }
                "ubuntu" {
                    sudo apt-get update
                    sudo apt-get install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev libbz2-dev tk-dev -y
                }
                "alpine" {
                    sudo apk add --update --no-cache alpine-sdk linux-headers zlib-dev bzip2-dev readline-dev sqlite-dev openssl-dev tk-dev libffi-dev
                }
                "fedora" {
                    sudo yum groupinstall "Development Tools" -y
                    sudo yum install zlib-devel bzip2-devel readline-devel sqlite-devel openssl-devel tk-devel libffi-devel -y
                }
                "centos" {
                    sudo yum groupinstall "Development Tools" -y
                    sudo yum install zlib-devel bzip2-devel readline-devel sqlite-devel openssl-devel tk-devel libffi-devel -y
                } default {
                    # Check for the presence of package managers and execute corresponding commands
                    if (Get-Command apt-get -ErrorAction SilentlyContinue) {
                        sudo apt-get update
                        sudo apt-get install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev libbz2-dev tk-dev -y
                    } elseif (Get-Command apk -ErrorAction SilentlyContinue) {
                        sudo apk add --update --no-cache alpine-sdk linux-headers zlib-dev bzip2-dev readline-dev sqlite-dev openssl-dev tk-dev libffi-dev
                    } elseif (Get-Command yum -ErrorAction SilentlyContinue) {
                        sudo yum groupinstall "Development Tools" -y
                        sudo yum install zlib-devel bzip2-devel readline-devel sqlite-devel openssl-devel tk-devel libffi-devel -y
                    } elseif (Get-Command dnf -ErrorAction SilentlyContinue) {
                        sudo dnf groupinstall "Development Tools" -y
                        sudo dnf install zlib-devel bzip2-devel readline-devel sqlite-devel openssl-devel tk-devel libffi-devel -y
                    } elseif (Get-Command zypper -ErrorAction SilentlyContinue) {
                        sudo zypper install -t pattern devel_basis
                        sudo zypper install zlib-devel bzip2-devel readline-devel sqlite3-devel openssl-devel tk-devel libffi-devel -y
                    } elseif (Get-Command pacman -ErrorAction SilentlyContinue) {
                        sudo pacman -Syu --noconfirm
                        sudo pacman -S base-devel zlib bzip2 readline sqlite openssl tk libffi --noconfirm
                    } elseif (Get-Command brew -ErrorAction SilentlyContinue) {
                        brew update
                        brew install zlib bzip2 readline sqlite openssl tk libffi
                    } elseif (Get-Command snap -ErrorAction SilentlyContinue) {
                        Write-Warning "Snap packages are not directly applicable for building Python. Please ensure build dependencies are installed using another package manager."
                    } elseif (Get-Command flatpak -ErrorAction SilentlyContinue) {
                        Write-Warning "Flatpak is not suitable for installing build dependencies. Please use another package manager."
                    } else {
                        Write-Warning "Compatible package manager not found. Please install the build dependencies manually."
                    }
                }
            }
            Python-Install-Unix-Source
        }
    } else {
        Write-Host "Cannot determine Linux distribution."
        exit 1
    }
}

function Python-Install-Unix-Source {
    Invoke-WebRequest -Uri https://www.python.org/ftp/python/3.8.18/Python-3.8.18.tgz -OutFile Python-3.8.18.tgz
    tar -xvf Python-3.8.18.tgz
    $current_working_dir = (Get-Location).Path
    Set-Location -LiteralPath "Python-3.8.18" -ErrorAction Stop
    $env:LDFLAGS="-Wl,-rpath=/usr/local/lib"
    sudo ./configure --enable-optimizations --with-ensurepip=install --enable-shared
    sudo make -j $(nproc)
    # Do NOT use `make install`. `make altinstall` will install it system-wide, but not as the default system python. (/usr/local/bin/python3.8)
    sudo make altinstall
    Set-Location -LiteralPath $current_working_dir
    # LD_LIBRARY_PATH must be updated. However this won't be permanent, just long enough to create the venv.
    $env:LD_LIBRARY_PATH = "/usr/local/lib:$env:LD_LIBRARY_PATH"
}

function Python-Install-Windows {
    Param (
        [string]$global:pythonVersion
    )
    try {
        # Download and install Python
        $pythonInstallerUrl = "https://www.python.org/ftp/python/$global:pythonVersion/python-$global:pythonVersion.exe"
        $installerPath = "$env:TEMP/python-$global:pythonVersion.exe"
        Write-Host "Downloading 'python-$global:pythonVersion.exe' to '$env:TEMP', please wait..."
        Invoke-WebRequest -Uri $pythonInstallerUrl -OutFile $installerPath
        Write-Host "Download completed."
        Write-Host "Installing 'python-$global:pythonVersion.exe', please wait..."
        Start-Process -FilePath $installerPath -Args '/quiet InstallAllUsers=0 PrependPath=1 InstallLauncherAllUsers=0' -Wait -NoNewWindow
        Write-Host "Python install process has finished."
    
        # Refresh environment variables to detect new Python installation
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
        return $true
    } catch {
        Write-Error "$($_.InvocationInfo.PositionMessage)`n$($_.Exception.Message)"
        return $false
    }
}

function Get-Python-Version {
    Param (
        [string]$pythonPath
    )
    try {
        if (Test-Path $pythonPath -ErrorAction SilentlyContinue) {
            $global:pythonVersionOutput = & $pythonPath --version 2>&1
            $global:pythonVersionString = $global:pythonVersionOutput -replace '^Python\s+'
            $numericVersionString = $global:pythonVersionString -replace '(\d+\.\d+\.\d+).*', '$1'
            $global:pythonVersion = [Version]$numericVersionString
            return $global:pythonVersion
        }
    } catch {
        return [Version]"0.0.0"
    }
}

$minVersion = [Version]"3.7.0"
$maxVersion = [Version]"3.13.0"
$recommendedVersion = [Version]"3.8.10"
$lessThanVersion = [Version]"3.9"

function Initialize-Python {
    Param (
        [string]$pythonPath
    )

    # Check Python version
    $global:pythonVersion = Get-Python-Version $pythonPath

    if ($global:pythonVersion -ge $minVersion -and $global:pythonVersion -le $lessThanVersion) {
        Write-Host "Python $global:pythonVersion install detected."
    } elseif ($global:pythonVersion -ge $minVersion) {
        Write-Warning "The Python version on PATH ($global:pythonVersion) is not fully tested, please consider using python 3.8. Continuing anyway..."
    } else {
        Write-Error "Your installed Python version '$global:pythonVersion' is not supported. Please install a python version between '$minVersion' and '$maxVersion'"
        Write-Host "Press any key to exit..."
        if (-not $noprompt) {
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        }
        exit
    }
}

$validPythonVersions = @("3.7", "3.8", "3.9", "3.10", "3.11", "3.12", "3.13", "3.14")

function Get-PythonPaths {
    Param (
        [string]$version
    )

    $windowsVersion = $version -replace '\.', ''  # "3.8" becomes "38"

    $windowsPaths = @(
        "C:\Program Files\Python$windowsVersion\python.exe",
        "C:\Program Files (x86)\Python$windowsVersion\python.exe",
        "C:\Program Files\Python$windowsVersion-32\python.exe",
        "C:\Program Files (x86)\Python$windowsVersion-32\python.exe",
        "$env:USERPROFILE\AppData\Local\Programs\Python\Python$windowsVersion\python.exe",
        "$env:USERPROFILE\AppData\Local\Programs\Python\Python$windowsVersion-32\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python$windowsVersion\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python$windowsVersion-32\python.exe"
    )

    $linuxAndMacPaths = @(
        "/usr/bin/python$version",
        "/usr/local/bin/python$version",
        "/bin/python$version",
        "/sbin/python$version",
        "~/.local/bin/python$version",
        "~/.pyenv/versions/$version/bin/python3",
        "~/.pyenv/versions/$version/bin/python",
        "/usr/local/Cellar/python/$version/bin/python3",  # Homebrew on macOS
        "/opt/local/bin/python$version",                  # MacPorts on macOS
        "/opt/python$version"                             # Custom installations
    )

    return @{ Windows = $windowsPaths; Linux = $linuxAndMacPaths; Darwin = $linuxAndMacPaths }
}

function Get-Path-From-Command {
    Param(
        [string]$command
    )
    $pythonCommand = Get-Command -Name $command -ErrorAction SilentlyContinue

    if ($null -ne $pythonCommand) {
        $pythonPath = $pythonCommand.Source
        Write-Host "Command: '$command' Path to Python executable: $pythonPath"
        return $pythonPath
    } else {
        return ""
    }
}

$global:pythonInstallPath = ""
$global:pythonVersion = ""

function Test-PythonCommand {
    param (
        [string]$CommandName
    )
    $pythonCommand = Get-Command -Name $CommandName -ErrorAction SilentlyContinue
    if ($null -ne $pythonCommand) {
        $testPath = Get-Path-From-Command $CommandName
        $global:pythonVersion = Get-Python-Version $testPath
        if ($global:pythonVersion -ge $minVersion -and $global:pythonVersion -lt $maxVersion) {
            Write-Host "Found python command with version $global:pythonVersion"
            $global:pythonInstallPath = Get-Path-From-Command $testPath
            return $true
        } else {
            Write-Host "python '$testPath' version '$global:pythonVersion' not supported"
            Clear-GlobalPythonVariablesIfNecessary
        }
    }
    return $false
}

function Find-Python {
    Param (
        [switch]$intrnal
    )
    # Check for Python 3 command and version
    $pythonVersions = @('python3.8', 'python3', 'python3.9', 'python3.10', 'python3.11', 'python3.12', 'python3.13', 'python3.14', 'python')
    foreach ($pyCommandPathCheck in $pythonVersions) {
        if (Test-PythonCommand -CommandName $pyCommandPathCheck) {
            return
        }
    }

    if ( $global:pythonInstallPath -eq "" -or ($global:pythonVersion -ne "" -and $global:pythonVersion -ge $recommendedVersion )) {

        foreach ($version in $validPythonVersions) {
            $paths = (Get-PythonPaths $version)[(Get-OS)]
            foreach ($path in $paths) {
                try {
                    # Resolve potential environment variables in the path
                    $resolvedPath = [Environment]::ExpandEnvironmentVariables($path)
                    if (Test-Path $resolvedPath -ErrorAction SilentlyContinue) {
                        $thisVersion = Get-Python-Version $resolvedPath
                        if ($thisVersion -ge $minVersion -and $thisVersion -le $maxVersion) {
                            # Valid path or better recommended path found.
                            if ($global:pythonInstallPath -eq "" -or $thisVersion -le $recommendedVersion) {
                                Write-Host "Found python install path with version $thisVersion at path '$resolvedPath'"
                                $global:pythonInstallPath = $resolvedPath
                                $global:pythonVersion = $thisVersion
                            }
                        }
                    }
                } catch {
                    Write-Host -ForegroundColor Red "$($_.InvocationInfo.PositionMessage)`n$($_.Exception.Message)"
                }
            }
        }
    }

    if ( $global:pythonInstallPath -eq "") {
        if (-not $intrnal) {
            if ( (Get-OS) -eq "Windows" ) {
                if (-not $noprompt) {
                    Write-Host "A supported Python version was not detected on your system. Install Python version $recommendedVersion now automatically?"
                    $userInput = Read-Host "(Y/N)"
                    if ( $userInput -ne "Y" -and $userInput -ne "y" ) {
                        Write-Host "A python install between versions $minVersion and $maxVersion is required for PyKotor."
                        Write-Host "Press any key to exit..."
                        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
                        exit
                    }
                    $installAttempted = Python-Install-Windows "3.8.10"
                    if ( $installAttempted -eq $false) {
                        Write-Host "The Python install either failed or has been cancelled."
                        Write-Host "A python install between versions $minVersion and $maxVersion is required for PyKotor."
                        Write-Host "Press any key to exit..."
                        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
                        exit
                    }
                }
            } elseif ( (Get-OS) -eq "Linux" ) {
                Install-Linux-Deps
            } elseif ( (Get-OS) -eq "Mac" ) {
                & bash -c "brew install python@3.12" 2>&1 | Write-Output
            }
            Write-Host "Find python again now that it's been installed."
            Find-Python -intrnal
        }
    }
    if ( -not $intrnal -and (Get-Linux-Distro-Name) -eq "ubuntu" -or (Get-Linux-Distro-Name) -eq "debian") {
        Install-Linux-Deps
    }
}

$venvPath = $repoRootPath + $pathSep + $venv_name
$findVenvExecutable = $true
if (Get-ChildItem Env:VIRTUAL_ENV -ErrorAction SilentlyContinue) {  # Check if a venv is already activated
    $venvPath = $env:VIRTUAL_ENV
    Write-Host "A virtual environment is currently activated: $venvPath"
    if ($null -ne $pythonExePath) { # check if this script itself was previously used to activate this venv.
        Write-Host "install_python_venv.ps1 has already ran and activated this venv, retrying anyway."
    }
    deactivate
} elseif ($venvPath -ne ($repoRootPath + $pathSep) -and (Test-Path $venvPath -ErrorAction SilentlyContinue)) {
    Write-Host "Found existing python virtual environment at '$venvPath'"
} else {
    Find-Python
    if ( $global:pythonInstallPath -eq "" ) {
        if ( -not $noprompt ) {
            Write-Warning "Could not find path to python. Try again?"
            $userInput = Read-Host "(Y/N)"
            if ( $userInput -ne "Y" -and $userInput -ne "y" ) {
                $userInput = Read-Host "Enter the path to python executable:"
                if ( Test-Path -Path $userInput -ErrorAction SilentlyContinue ) {
                    $global:pythonInstallPath = $userInput
                } else {
                    Write-Error "Python executable not found at '$userInput'"
                    Write-Host "Press any key to exit..."
                    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
                    exit
                }
            } else {
                Find-Python
            }
        } else {
            Write-Error "Could not find path to python."
            exit
        }
    }
    Write-Host "Attempting to create a python virtual environment. This might take a while..."
    $pythonVenvCreation = & $global:pythonInstallPath -m venv $venvPath 2>&1
    if ($pythonVenvCreation -like "*Error*") {
        Write-Error $pythonVenvCreation
        Write-Error "Failed to create virtual environment. Ensure Python 3.8 is installed correctly."
        Write-Warning "Attempt to use main python install at $global:pythonInstallPath instead of a venv? (not recommended but is usually fine)"
        if (-not $noprompt) {
            $userInput = Read-Host "(Y/N)"
            if ( $userInput -ne "Y" -and $userInput -ne "y" ) {
                Write-Host "Press any key to exit..."
                $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
                exit
            }
        }
        $pythonExePath = $global:pythonInstallPath
        $findVenvExecutable = $false
    } else {
        #Write-Host $pythonVenvCreation
        Write-Host "Virtual environment created."
    }
}

if ( $findVenvExecutable -eq $true) {
    # Define potential paths for Python executable within the virtual environment
    $pythonExePaths = switch ((Get-OS)) {
        'Windows' { @("$venvPath\Scripts\python.exe") }
        'Linux' { @("$venvPath/bin/python3", "$venvPath/bin/python") }
        'Mac' { @("$venvPath/bin/python3", "$venvPath/bin/python") }
    }

    # Find the Python executable
    $pythonExePath = $pythonExePaths | Where-Object { Test-Path $_ } | Select-Object -First 1
    if ($null -ne $pythonExePath) {
        Write-Host "Python venv executable found at '$pythonExePath'"
    } else {
        Write-Error "No python executables found in virtual environment."
        Write-Error "Not found: [$pythonExePaths]"
        Write-Host "Press any key to exit..."
        if (-not $noprompt) {
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        }
        exit
    }
}


Write-Host "Activating venv at '$venvPath'"
if ((Get-OS) -eq "Windows") {
    # For Windows, attempt to activate using Activate.ps1
    $activateScriptPath = Join-Path -Path $venvPath -ChildPath "Scripts\Activate.ps1"
    if (Test-Path $activateScriptPath) {
        & $activateScriptPath
    } else {
        Write-Error "Activate.ps1 not found in $activateScriptPath"
        Write-Host "Press any key to exit..."
        if (-not $noprompt) {
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        }
        exit
    }
} else {
    # For Linux and macOS, check for Activate.ps1 for consistency, though it's not usually present
    $activateScriptPath = Join-Path -Path $venvPath -ChildPath "bin/Activate.ps1"
    if (Test-Path $activateScriptPath -ErrorAction SilentlyContinue) {
        & $activateScriptPath
    } else {
        Write-Warning "Activate.ps1 not found in $activateScriptPath, attempting to use fallback activation script..."
        $bashCommand = "source " + (Join-Path -Path $venvPath -ChildPath "bin/activate")
        bash -c "`"$bashCommand`""
        Write-Host "Activated venv using bash source command."
    }
}

Initialize-Python $pythonExePath

# Set environment variables from .env file
$dotenv_path = "$repoRootPath$pathSep.env"
Write-Host "Loading project environment variables from '$dotenv_path'"
$envFileFound = Set-EnvironmentVariablesFromEnvFile "$dotenv_path"
if ($envFileFound) {
    Write-Host ".env file has been loaded into session."
} else {
    Write-Warning "'$dotenv_path' file not found, this may mean you need to fetch the repo's latest changes. Please resolve this problem and try again."
    Write-Host "Press any key to exit..."
    if (-not $noprompt) {
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
    exit
}
