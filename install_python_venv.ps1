param (
  [switch]$noprompt
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
    $global:pythonVersionOutput = & $pythonPath --version 2>&1
    $global:pythonVersionString = $global:pythonVersionOutput -replace '^Python\s+'
    $numericVersionString = $global:pythonVersionString -replace '(\d+\.\d+\.\d+).*', '$1'
    $global:pythonVersion = [Version]$numericVersionString
    return $global:pythonVersion
}

$minVersion = [Version]"3.8.0"
$maxVersion = [Version]"3.12.0"
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
        Write-Warning "The Python version on PATH ($global:pythonVersion) is not recommended, please use python 3.8. Continuing anyway..."
    } else {
        Write-Error "Your installed Python version '$global:pythonVersion' is not supported. Please install a python version between '$minVersion' and '$maxVersion'"
        Write-Host "Press any key to exit..."
        if (-not $noprompt) {
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        }
        exit
    }
}

$validPythonVersions = @("3.8", "3.9", "3.10", "3.11", "3.12")

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
        Write-Host "Path to Python executable: $pythonPath"
        return $pythonPath
    } else {
        return ""
    }
}

$global:pythonInstallPath = ""
$global:pythonVersion = ""

function Find-Python {
    Param (
        [switch]$intrnal
    )
    # Check for Python 3 command and version
    $python3Command = Get-Command -Name python3 -ErrorAction SilentlyContinue
    if ($null -ne $python3Command) {
        $global:pythonVersion = Get-Python-Version "python3"
        if ($global:pythonVersion -ge $minVersion -and $global:pythonVersion -lt $maxVersion) {
            Write-Host "Found python3 command"
            $global:pythonInstallPath = Get-Path-From-Command "python3"
        } else {
            $global:pythonInstallPath = ""
            $global:pythonVersion = ""
        }
    }

    $pythonCommand = Get-Command -Name python -ErrorAction SilentlyContinue
    if ($null -ne $pythonCommand) {
        $global:pythonVersion = Get-Python-Version "python"
        if ($global:pythonVersion -ge $minVersion -and $global:pythonVersion -lt $maxVersion) {
            Write-Host "Found python command with version $global:pythonVersion"
            $global:pythonInstallPath = Get-Path-From-Command "python"
        } else {
            $global:pythonInstallPath = ""
            $global:pythonVersion = ""
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
                if (Test-Path "/etc/os-release") {
                    $osInfo = Get-Content "/etc/os-release" -Raw
                    if ($osInfo -match 'ID=(.*)') {
                        $distro = $Matches[1].Trim('"')
                    }
                    if ($osInfo -match 'VERSION_ID=(.*)') {
                        $versionId = $Matches[1].Trim('"')
                    }
                    
                    try {
                        switch ($distro) {
                            "debian" {
                                sudo apt update
                                sudo apt install python3 -y
                                sudo apt install python3-dev -y
                                sudo apt install python3-venv -y
                                sudo apt install python3-pip -y
                                break
                            }
                            "ubuntu" {
                                sudo apt install python3 -y
                                sudo apt install python3-dev -y
                                sudo apt install python3-venv -y
                                sudo apt install python3-pip -y
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
                            "fedora" {
                                sudo dnf update
                                sudo dnf install python3 -y
                                sudo dnf install python3-pip -y
                                sudo dnf install python3-venv -y
                                break
                            }
                            "centos" {
                                sudo yum update
                                if ( $versionId -eq "7" ) {
                                    sudo yum install epel-release -y
                                }
                                sudo yum install python3 -y
                                sudo yum install python3-pip
                                sudo yum install python3-venv
                                break
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
                                sudo apt update
                                sudo apt install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev libbz2-dev tk-dev -y
                            }
                            "ubuntu" {
                                sudo apt update
                                sudo apt install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev libbz2-dev tk-dev -y
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
                            }
                            default {
                                Write-Error "Unsupported Linux distribution for building Python"
                                exit 1
                            }
                        }
                        Invoke-WebRequest -Uri https://www.python.org/ftp/python/3.8.18/Python-3.8.18.tgz
                        tar -xvf Python-3.8.18.tgz
                        $current_working_dir = (Get-Location).Path
                        Set-Location -LiteralPath "Python-3.8.18" -ErrorAction Stop
                        sudo ./configure --enable-optimizations
                        sudo make -j $(nproc)
                        sudo make altinstall
                        Set-Location -LiteralPath $current_working_dir
                    }
                } else {
                    Write-Host "Cannot determine Linux distribution."
                    exit 1
                }
            } elseif ( (Get-OS) -eq "Mac" ) {
                & bash -c "brew install python@3.8 -y" 2>&1 | Write-Output
            }
            Write-Host "Find python again now that it's been installed."
            Find-Python -intrnal
        } else {
            Write-Host "Find python again now that it's been installed."
            Find-Python -intrnal
        }
    }
}

$venvPath = "$repoRootPath$pathSep.venv"
$pythonExePath = ""
$findVenvExecutable = $true
if (Test-Path $venvPath -ErrorAction SilentlyContinue) {
    Write-Host "Found existing .venv at '$venvPath'"
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
    $pythonVenvCreation = & $global:pythonInstallPath -m venv $venvPath
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
    . $venvPath\Scripts\Activate.ps1
} else {
    . $venvPath/bin/Activate.ps1
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
