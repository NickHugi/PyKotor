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
        $installerPath = (Resolve-Path -LiteralPath "$env:TEMP/python-$global:pythonVersion.exe").Path
        Invoke-WebRequest -Uri $pythonInstallerUrl -OutFile $installerPath
        Start-Process -FilePath $installerPath -Args '/quiet InstallAllUsers=1 PrependPath=1' -Wait -NoNewWindow
    
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
        "C:\Program Files (x86)\Python$windowsVersion\python.exe",
        "C:\Program Files\Python$windowsVersion\python.exe",
        "$env:USERPROFILE\AppData\Local\Programs\Python\Python$windowsVersion\python.exe"
    )

    $linuxAndMacPaths = @(
        "/usr/bin/python$version",
        "/usr/local/bin/python$version",
        "~/.local/bin/python$version",
        "~/.pyenv/versions/$version/bin/python3",
        "~/.pyenv/versions/$version/bin/python"
    )

    return @{ Windows = $windowsPaths; Linux = $linuxAndMacPaths; Darwin = $linuxAndMacPaths }
}

function Get-Python-Path-From-Command {
    Param(
        [string]$command
    )
    $pythonCommand = Get-Command -Name python3 -ErrorAction SilentlyContinue

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
            $global:pythonInstallPath = Get-Python-Path-From-Command "python3"
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
            $global:pythonInstallPath = Get-Python-Path-From-Command "python"
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
        Write-Host "A supported Python version was not detected on your system. Install $recommendedVersion now automatically?"
        if (-not $noprompt) {
            $userInput = Read-Host "(Y/N)"
            if ( $userInput -ne "Y" -and $userInput -ne "y" ) {
                Write-Host "A python install between versions $minVersion and $maxVersion is required for PyKotor."
                Write-Host "Press any key to exit..."
                $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
                exit
            }
        }
        if (-not $intrnal) {
            if ( (Get-OS) -eq "Windows" ) {
                Python-Install-Windows "3.8.10"
            } elseif ( (Get-OS) -eq "Linux" ) {
                & bash -c "sudo apt install python3 -y" 2>&1 | Write-Output
                & bash -c "sudo apt install python3-dev -y" 2>&1 | Write-Output
            } elseif ( (Get-OS) -eq "Mac" ) {
                & bash -c "brew install python@3.8 -y" 2>&1 | Write-Output
            }
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
    # Attempt to create a virtual environment
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
