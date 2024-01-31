param (
  [switch]$noprompt
)

# Function to get the Operating System
function Get-OS {
    if ($IsWindows) { return "Windows" }
    elseif ($IsMacOS) { return "Mac" }
    elseif ($IsLinux) { return "Linux" }
    $os = (Get-WmiObject -Class Win32_OperatingSystem).Caption
    if ($os -match "Windows") { return "Windows" }
    elseif ($os -match "Mac") { return "Mac" }
    elseif ($os -match "Linux") { return "Linux" }
    PromptAndExit "Unknown Operating System"
}

# Function to prompt and exit if necessary
function PromptAndExit {
    Param ([string]$message)
    Write-Error $message
    Write-Host "Press any key to exit..."
    if (-not $noprompt) { $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") }
    exit
}


# Function to check for admin rights on Windows
function Check-AdminRights {
    if ((Get-OS) -eq "Windows" -and -not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
        Write-Warning "Please run PowerShell with administrator rights!"
        return $false
    }
    return $true
}

# Function to parse and set environment variables from .env file
function Set-EnvironmentVariablesFromEnvFile {
    Param ([string]$envFilePath)
    if (-not (Test-Path $envFilePath)) { 
        Write-Debug "Environment file not found."
        return $false 
    }

    Get-Content $envFilePath | ForEach-Object {
        if ($_ -match '^\s*(\w+)\s*=\s*(?:"(.*?)"|''(.*?)''|(.*?))\s*$') {
            ProcessEnvLine $matches
        }
    }
    Write-Host "Environment variables set from .env file."
    return $true
}

# Function to process each line of the environment file
function ProcessEnvLine {
    Param ([hashtable]$envmatches)
    $key, $value = $envmatches[1], $envmatches[2] + $envmatches[3] + $envmatches[4]

    Write-Debug "Processing variable: $key"
    Write-Debug "Retrieved from regex - Key: $key, Value: $value"

    $originalValue = $value
    ResolveAndSetEnvVariable $key $value $originalValue
}

# Function to resolve and set environment variables
function ResolveAndSetEnvVariable {
    Param ([string]$key, [string]$value, [string]$originalValue)
    $value = ResolveEnvVarsInValue $value $originalValue
    $value = GetUniquePathsFromValue $value
    Write-Host "Set environment variable $key from '${$env:$key}' to '$value'"
    Set-Item -Path "env:$key" -Value $value
}

# Function to resolve environment variables in the given value
function ResolveEnvVarsInValue {
    Param ([string]$value, [string]$originalValue)
    return $value -replace '\$\{env:(.*?)\}', {
        $envVarName = $matches[1]
        $retrievedEnvValue = [System.Environment]::GetEnvironmentVariable($envVarName, [System.EnvironmentVariableTarget]::Process)
        Write-Host "Replacing $envVarName '${env:$envVarName}' with '$retrievedEnvValue' in original value: $originalValue"
        if ($null -eq $retrievedEnvValue) { "" } else { $retrievedEnvValue }
    }
}

# Function to get unique paths from the given value
function GetUniquePathsFromValue {
    Param ([string]$value)
    $uniquePaths = @{}
    ($value -split ';').ForEach({
        $trimmedPath = $_.Trim()
        if (-not [string]::IsNullOrWhiteSpace($trimmedPath)) {
            Write-Debug "Trimmed Path: $trimmedPath"
            $absolutePath = "$repoRootPath/$trimmedPath"
            if (Test-Path $absolutePath) {
                $resolvedPath = (Resolve-Path -LiteralPath $absolutePath).Path
                Write-Debug "Resolved Path: $resolvedPath"
                if ($null -ne $resolvedPath) { $uniquePaths[$resolvedPath] = $true }
            }
        }
    })
    $finalValue = ($uniquePaths.Keys -join ';')
    Write-Debug "Original value: $value, Final value: $finalValue"
    return $finalValue
}

function Python-Install-Windows {
    Param (
        [string]$pythonVersion
    )
    try {
        # Download and install Python
        $pythonInstallerUrl = "https://www.python.org/ftp/python/$pythonVersion/python-$pythonVersion.exe"
        $installerPath = "$env:TEMP/python-$pythonVersion.exe"
        Write-Host "Downloading 'python-$pythonVersion.exe' to '$env:TEMP', please wait..."
        Invoke-WebRequest -Uri $pythonInstallerUrl -OutFile $installerPath
        Write-Host "Download completed."
        Write-Host "Installing 'python-$pythonVersion.exe', please wait..."
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
        $pythonVersionOutput = & $pythonPath --version 2>&1
        $pythonVersionString = $pythonVersionOutput -replace '^Python\s+'
        $numericVersionString = $pythonVersionString -replace '(\d+\.\d+\.\d+).*', '$1'
        $pythonVersion = [Version]$numericVersionString
        return $pythonVersion
    } catch {
        Write-Error "$($_.InvocationInfo.PositionMessage)`n$($_.Exception.Message)"
        return $null
    }
}

function Initialize-Python {
    Param (
        [string]$pythonPath
    )

    # Check Python version
    $pythonVersion = Get-Python-Version $pythonPath

    if ($pythonVersion -ge $minVersion -and $pythonVersion -le $lessThanVersion) {
        Write-Host "Python $pythonVersion install detected."
    } elseif ($pythonVersion -ge $minVersion) {
        Write-Warning "The Python version on PATH ($pythonVersion) is not recommended, please use python 3.8. Continuing anyway..."
    } else {
        PromptAndExit "Your installed Python version '$pythonVersion' is not supported. Please install a python version between '$minVersion' and '$maxVersion'"
    }
}

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

function Get-LinuxOSInfo {
    if (Test-Path "/etc/os-release") {
        $osInfo = Get-Content "/etc/os-release" -Raw
        $distro = $null
        $versionId = $null
        if ($osInfo -match 'ID=(.*)') {
            $distro = $Matches[1].Trim('"')
        }
        if ($osInfo -match 'VERSION_ID=(.*)') {
            $versionId = $Matches[1].Trim('"')
        }
        return @{ Distro = $distro; VersionId = $versionId }
    } else {
        Write-Error "Cannot determine Linux distribution."
        exit 1
    }
}

function InstallPythonOnLinux {
    $osInfo = Get-LinuxOSInfo
    $installCommands = @()

    if ($osInfo.Distro -eq "ubuntu" -or $osInfo.Distro -eq "debian") {
        $installCommands = @(
            'sudo apt update',
            'sudo apt install python3 -y',
            'sudo apt install python3-dev -y',
            'sudo apt install python3-venv -y',
            'sudo apt install python3-pip -y'
        )
    }
    elseif ($osInfo.Distro -eq "alpine") {
        $installCommands = @(
            'sudo apk update',
            'sudo apk add --update --no-cache python3',
            'ln -sf python3 /usr/bin/python',
            'python3 -m ensurepip',
            'pip3 install --no-cache --upgrade pip setuptools'
        )
    }
    elseif ($osInfo.Distro -eq "fedora" -or $osInfo.Distro -eq "centos") {
        $installCommands = @(
            'sudo dnf update',
            'sudo dnf install python3 -y',
            'sudo dnf install python3-pip -y',
            'sudo dnf install python3-venv -y'
        )
    }
    else {
        Write-Error "Unsupported Linux distribution"
        exit 1
    }
    foreach ($cmd in $installCommands) {
        Write-Debug $cmd
        Invoke-Expression $cmd
        if ($LASTEXITCODE -ne 0) {
            return $false
        }
    }
    $path = Get-Path-From-Command "python3"
    if (Test-Path $path -ErrorAction Ignore) {
        return $true
    }
    return $false
}

function PromptUser([string]$message) {
    while ($true) {
        if ( $noprompt -eq $true ) {
            Write-Host $message
            return $true
        }
        $userInput = Read-Host "$message (Y/N)"
        switch -Regex ($userInput.ToLower()) {
            '^y(es)?$' { return $true }
            '^n(o)?$'  { return $false }
            default    { Write-Host "Please type a valid option." }
        }
    }
}

function Get-Path-From-Command {
    $command = Get-Command -Name $commandName -ErrorAction SilentlyContinue
    if ($null -ne $command) {
        return $command.Source
    }
    return $null
}


function FindPythonInDefaultPaths {
    Param (
        [string[]]$validPythonVersions,
        [float]$minVersion,
        [float]$maxVersion,
        [float]$recommendedVersion
    )
    $foundPath = $null
    $foundVersion = $null

    foreach ($version in $validPythonVersions) {
        $paths = (Get-PythonPaths $version)[(Get-OS)]
        foreach ($path in $paths) {
            try {
                $resolvedPath = [Environment]::ExpandEnvironmentVariables($path)
                if (Test-Path $resolvedPath -ErrorAction SilentlyContinue) {
                    $thisVersion = Get-Python-Version $resolvedPath
                    if ($null -ne $thisVersion -and $thisVersion -ge $minVersion -and $thisVersion -le $maxVersion) {
                        if ($null -eq $foundPath -or $thisVersion -le $recommendedVersion) {
                            $foundPath = $resolvedPath
                            $foundVersion = $thisVersion
                        }
                    }
                }
            } catch {
                Write-Host -ForegroundColor Red "$($_.InvocationInfo.PositionMessage)`n$($_.Exception.Message)"
            }
        }
    }
    return @{ "Path" = $foundPath; "Version" = $foundVersion }
}


function GetPythonCommandInfo {
    Param (
        [string]$commandName
    )
    $command = Get-Command -Name $commandName -ErrorAction SilentlyContinue
    if ($null -ne $command) {
        $version = Get-Python-Version $commandName
        $path = Get-Path-From-Command $commandName
        return @{
            "Path" = $path;
            "Version" = $version;
        }
    }
    return $null
}


function Find-Python {
    Param (
        [string[]]$validPythonVersions,
        [float]$minVersion,
        [float]$maxVersion,
        [float]$recommendedVersion
    )
    $bestVersion = $null
    $bestPath = $null

    # Check for python/python3 commands on path.
    $python3CmdInfo = GetPythonCommandInfo "python3"
    if ($null -ne $python3CmdInfo) {
        $bestVersion = $python3CmdInfo.Version
        $bestPath = $python3CmdInfo.Path
        Write-Host "python install (version $bestVersion) found at '$bestPath'"
    }
    $pythonCmdInfo = GetPythonCommandInfo "python3"
    if ($null -ne $pythonCmdInfo) {
        $bestVersion = $pythonCmdInfo.Version
        $bestPath = $pythonCmdInfo.Path
        Write-Host "python3 install (version $bestVersion) found at '$bestPath'"
    }

    if ( $null -eq $bestPath -or ($null -ne $bestVersion -and $bestVersion -gt $recommendedVersion )) {
        $nextBestPythonInfo = FindPythonInDefaultPaths $validPythonVersions $minVersion $maxVersion $recommendedVersion
        if ( $null -ne $nextBestPythonInfo.Path -and $nextBestPythonInfo.Version -le $recommendedVersion ) {
            $bestVersion = $nextBestPythonInfo.Version
            $bestPath = $nextBestPythonInfo.Path
            Write-Host "python install (version $bestVersion) found at '$bestPath'"
        }
    }
    return @{ "Path" = $bestPath; "Version" = $bestVersion }
}

Check-AdminRights
$repoRootPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pathSep = if ((Get-OS) -eq "Windows") { "\" } else { "/" }

$venvPath = "$repoRootPath$pathSep.venv"
$pythonExePath = ""
$findVenvExecutable = $true

$minVersion = [Version]"3.8.0"
$maxVersion = [Version]"3.12.0"
$recommendedVersion = [Version]"3.8.10"
$validPythonVersions = @("3.8", "3.9", "3.10", "3.11", "3.12")
if (Test-Path $venvPath -ErrorAction SilentlyContinue) {
    Write-Host "Found existing .venv at '$venvPath'"
} else {
    $pythonInfo = Find-Python $validPythonVersions $minVersion $maxVersion $recommendedVersion
    if ( $null -eq $pythonInfo.Path ) {
        if ((Get-OS) -eq "Windows") {
            Python-Install-Windows
        } else {
            InstallPythonOnLinux
        }
        $pythonInfo = Find-Python $validPythonVersions $minVersion $maxVersion $recommendedVersion
        if ( $null -eq $pythonInfo.Path ) {
            if ( $noprompt -eq $true) {
                PromptAndExit "Could not find path to python."
            } else {
                $userInput = PromptUser "Could not find path to python. Try again?"
                if ( $userInput -eq $false ) {
                    $userInput = Read-Host "Enter the path to your python executable:"
                    if ( Test-Path -Path $userInput -ErrorAction SilentlyContinue ) {
                        $pythonInfo = GetPythonCommandInfo $userInput
                    } else {
                        PromptAndExit "Python is required, please install it then try running this script again."
                    }
                } else {
                    Find-Python
                }
            }
        }
    }
    Write-Host "Attempting to create a python virtual environment. This might take a while..."
    $pythonVenvCreation = & $pythonInfo.Path -m venv $venvPath
    if ($pythonVenvCreation -like "*Error*") {
        Write-Error $pythonVenvCreation
        Write-Error "Failed to create python venv. Ensure a valid version of Python compatible with PyKotor is installed correctly."
        $tempPath = $pythonInfo.Path
        $response = PromptUser "Attempt to use main python install at '$tempPath' instead of a venv? (not recommended but is usually fine)"
        if (-not $response) {
            PromptAndExit "You chose to exit, Goodbye!"
        } else {
            $pythonExePath = $pythonInfo.Path
            $findVenvExecutable = $false
        }
    } else {
        Write-Debug $pythonVenvCreation
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
