#!/usr/bin/env pwsh

[CmdletBinding(PositionalBinding=$false)]
param(
  [switch]$noprompt,
  [string]$venv_name = ".venv",
  [string]$force_python_version
)
$global:force_python_version = $force_python_version

$latestPipVersion = "24.0"
$latestPipPackageUrl = "https://files.pythonhosted.org/packages/94/59/6638090c25e9bc4ce0c42817b5a234e183872a1129735a9330c472cc2056/pip-$latestPipVersion.tar.gz"
$latestSetuptoolsVersion = "69.2.0"
$latestSetuptoolsUrl = "https://files.pythonhosted.org/packages/4d/5b/dc575711b6b8f2f866131a40d053e30e962e633b332acf7cd2c24843d83d/setuptools-$latestSetuptoolsVersion.tar.gz"

$global:pythonInstallPath = ""
$global:pythonVersion = ""

$scriptPath = $MyInvocation.MyCommand.Definition  # Absolute path to this script.
$repoRootPath = (Resolve-Path -LiteralPath "$scriptPath/..").Path  # Path to PyKotor repo root.
Write-Host "The path to the script directory is: $scriptPath"
Write-Host "The path to the root directory is: $repoRootPath"

function Handle-Error {
    param (
        [Parameter(Mandatory=$true)]
        [System.Management.Automation.ErrorRecord]$ErrorRecord
    )

    Write-Host -ForegroundColor Red "Detailed Error Report:"
    Write-Host -ForegroundColor Red "Message: $($ErrorRecord.Exception.Message)"
            
    # Attempt to provide a more detailed location of the error
    if ($ErrorRecord.InvocationInfo -and $ErrorRecord.InvocationInfo.MyCommand) {
        Write-Host -ForegroundColor Red "Command Name: $($ErrorRecord.InvocationInfo.MyCommand.Name)"
        Write-Host -ForegroundColor Red "Script Name: $($ErrorRecord.InvocationInfo.ScriptName)"
        Write-Host -ForegroundColor Red "Line Number: $($ErrorRecord.InvocationInfo.ScriptLineNumber)"
        Write-Host -ForegroundColor Red "Line: $($ErrorRecord.InvocationInfo.Line)"
    } else {
        Write-Host -ForegroundColor Red "No invocation information available."
    }

    # Extract and display the script stack trace if available
    if ($ErrorRecord.ScriptStackTrace) {
        Write-Host -ForegroundColor Red "Script Stack Trace:"
        Write-Host -ForegroundColor Red $ErrorRecord.ScriptStackTrace
    } else {
        Write-Host -ForegroundColor Red "No script stack trace available."
    }
}

trap {
    Write-Error "An error occurred: $_"
    $response = Read-Host "Press Enter to continue or type 'q' or the hotkey `ctrl+c` to quit."
    if ($response -eq 'exit') { exit }
    continue
}

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


function Invoke-BashCommand {
    param (
        [string]$Command
    )

    try {
        # Execute the bash command and capture its output
        $output = & bash -c $Command 2>&1
        # Check if the command was successful
        if (-not $? -or $LASTEXITCODE -ne 0) {
            $errorMessage = "Bash command `'$Command`' failed with exit code $LASTEXITCODE. Output: $output"
            # Throw an exception with the error message
            throw $errorMessage
        }
    } catch {
        # Rethrow the caught exception after adding more context
        throw "Failed to execute Bash command `'$Command`'. Error: $_"
    }
    # Return the captured output if successful
    return $output
}

$pathSep = "/"
if ((Get-OS) -eq "Windows") {
    $pathSep = "\"
} else {
    # LD_LIBRARY_PATH must be set on unix systems.
    $ldLibraryPath = [System.Environment]::GetEnvironmentVariable('LD_LIBRARY_PATH', 'Process')
    if ([string]::IsNullOrEmpty($ldLibraryPath)) {
        Write-Warning "LD_LIBRARY_PATH not defined, creating it with /usr/lib:/usr/local/lib ..."
        [System.Environment]::SetEnvironmentVariable('LD_LIBRARY_PATH', '/usr/lib:/usr/local/lib', 'Process')
    } elseif (-not $ldLibraryPath.Contains('/usr/local/lib')) {
        Write-Warning "LD_LIBRARY_PATH defined but no definition for /usr/local/lib, adding it now..."
        $newLdLibraryPath = $ldLibraryPath + ':/usr/local/lib'
        if (-not $newLdLibraryPath.Contains('/usr/lib')) {
            Write-Host "Also adding /usr/lib"
            $newLdLibraryPath = $ldLibraryPath + ':/usr/lib'
        }
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
    if (Test-Path -LiteralPath $envFilePath) {
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
                        if ( Test-Path -LiteralPath $absolutePath -ErrorAction SilentlyContinue )
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
                Write-Host "`$env:$key='$value'"
                Set-Item -LiteralPath "env:$key" -Value $value
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

# Helper function to run a command and capture output with a timeout
function Invoke-WithTimeout {
    param(
        [ScriptBlock]$ScriptBlock,
        [TimeSpan]$Timeout
    )
    $ps = [powershell]::Create().AddScript($ScriptBlock)
    $task = $ps.BeginInvoke()
    if ($task.AsyncWaitHandle.WaitOne($Timeout)) {
        $output = $ps.EndInvoke($task)
        $ps.Dispose()
        return $output
    } else {
        $ps.Dispose()
        throw "Command timed out."
    }
}


# Needed for tkinter-based apps, common in Python and subsequently most of PyKotor's tools.
function Install-TclTk {
    function GetAndCompareVersion($command, $scriptCommand, $requiredVersion) {
        $commandInfo = Get-Command -Name $command -ErrorAction SilentlyContinue
        if (-not ($commandInfo)) {
            Write-Host "'$command' not found during CommandExists check."
            # Attempt to find version-specific command if 'wish' is not found
            if ($command -eq 'wish') {
                $versionSpecificCommand = Get-Command 'wish*' -ErrorAction SilentlyContinue | Select-Object -First 1
                if ($null -ne $versionSpecificCommand) {
                    $command = $versionSpecificCommand.Name
                    Write-Host "'wish' command not found but versioned '$command' was found. Symlinking $($versionSpecificCommand.Source) >> /usr/local/bin/wish"
                    Invoke-BashCommand "sudo ln -sv $($versionSpecificCommand.Source) /usr/local/bin/wish"
                } else {
                    Write-Host "Command 'wish' not found."
                    return $false
                }
            } else {
                Write-Host "Command '$command' not found."
                return $false
            }
        } else {
            Write-Host "Command info for $command"
            Write-Host $commandInfo
            Write-Host $commandInfo.Path
            Write-Host $commandInfo.Name
        }
    
        try {
            $versionScript = "echo `$scriptCommand` | $command"
            $versionString = Invoke-Expression $versionScript 2>&1
            if ([string]::IsNullOrWhiteSpace($versionString)) {
                Write-Host "No version output detected for '$command'."
                return $false
            }
            $versionString = $versionString -replace '[^\d.]+', ''  # Clean the version string of non-numeric characters
            Write-Host "Output of $command : '$versionString'"
    
            if ($versionString -eq '') {
                Write-Host "Version string for '$command' is empty."
                return $false
            }
    
            $version = New-Object System.Version $versionString.Trim()
            return $version -ge $requiredVersion
        } catch {
            Handle-Error -ErrorRecord $_
            return $false
        }
    }
    
    # Correctly invoke tclsh and wish with the version check script
    $tclVersionScript = "puts [info patchlevel];exit"
    $tkVersionScript = "puts [info patchlevel];exit"
    
    # Initialize required version
    $recommendedVersion = "8.6.10"
    if ((Get-OS) -eq "macOS") {
        $requiredVersion = New-Object -TypeName "System.Version" $recommendedVersion
    } else {
        $requiredVersion = New-Object -TypeName "System.Version" "8.6.0"
    }
    
    # Perform version checks
    $tclCheck = GetAndCompareVersion "tclsh" $tclVersionScript $requiredVersion
    $tkCheck = GetAndCompareVersion "wish" $tkVersionScript $requiredVersion

    # Handle the result of the version checks
    if ($tclCheck -and $tkCheck) {
        Write-Host "Tcl and Tk version $requiredVersion or higher are already installed."
        return
    } else {
        Write-Host "Tcl/Tk version must be updated now."
    }

    if ((Get-OS) -eq "Mac") {
        #  OSSpinLock is deprecated in favor of os_unfair_lock starting with 10.12. I can't modify the src of tcl here so this'll just need to brew it.
        # More info: https://www.python.org/download/mac/tcltk/
        # Retrieve current macOS version
        $macOSVersion = Invoke-BashCommand -Command "sw_vers -productVersion"
        $majorMacOSVersion = [int]$macOSVersion.Split('.')[0]
        $minorMacOSVersion = [int]$macOSVersion.Split('.')[1]
        if (($majorMacOSVersion -eq 10 -and $minorMacOSVersion -ge 12) -or $majorMacOSVersion -gt 10) {
            bash -c 'brew install tcl-tk --overwrite --force || true'
            Write-Host '"brew install tcl-tk --overwrite --force || true" completed.'
            $tclCheck = GetAndCompareVersion "tclsh", $tclVersionScript, $requiredVersion
            $tkCheck = GetAndCompareVersion "wish", $tkVersionScript, $requiredVersion
    
            if ($tclCheck -and $tkCheck) {
                Write-Host "Tcl and Tk version $requiredVersion or higher are already installed."
                return
            } else {
                Write-Error "Could not get tcl/tk versions after brew install!"
            }
            return
        }
    }

    Write-Host "Installing Tcl from source..."
    $originalDir = Get-Location
    Invoke-BashCommand "curl -O -L https://prdownloads.sourceforge.net/tcl/tcl$recommendedVersion-src.tar.gz"
    Invoke-BashCommand "tar -xzvf tcl$recommendedVersion-src.tar.gz"
    Set-Location "tcl$recommendedVersion/unix"
    Invoke-BashCommand "./configure --prefix=/usr/local"
    Invoke-BashCommand "make"
    Invoke-BashCommand "sudo make install"

    Set-Location $originalDir
    Write-Host "Installing Tk from source..."
    Invoke-BashCommand "curl -O -L https://prdownloads.sourceforge.net/tcl/tk$recommendedVersion-src.tar.gz"
    Invoke-BashCommand "tar -xzvf tk$recommendedVersion-src.tar.gz"
    Set-Location "tk$recommendedVersion/unix"
    Invoke-BashCommand "./configure --prefix=/usr/local --with-tcl=/usr/local/lib"
    Invoke-BashCommand "make"
    Invoke-BashCommand "sudo make install"
    Set-Location $originalDir

    # Refresh the env after installing tcl/tk
    #$userPath = [System.Environment]::GetEnvironmentVariable("PATH", [System.EnvironmentVariableTarget]::User)
    #$systemPath = [System.Environment]::GetEnvironmentVariable("PATH", [System.EnvironmentVariableTarget]::Machine)
    #$env:PATH = $userPath + ";" + $systemPath
    
    # Perform version checks
    $tclCheck = GetAndCompareVersion "tclsh" $tclVersionScript $requiredVersion
    $tkCheck = GetAndCompareVersion "wish" $tkVersionScript $requiredVersion

    # Handle the result of the version checks
    if ($tclCheck -and $tkCheck) {
        Write-Host "Tcl and Tk version $requiredVersion or higher have been installed."
        return
    } else {
        if ((Get-OS) -ne "Linux") {
            Write-Error "Tcl/Tk could not be installed! See above logs for the issue"
        } else {
            Write-Warning "Known problem with wish on linux, assuming it's installed and continuing..."
        }
    }
}

function Install-Python-Linux {
    Param (
        [string]$pythonVersion="3",  # MAJOR.MINOR!!!
        [bool]$skipSource
    )

    # Set default value if null or empty string is passed
    if (-not $pythonVersion) {
        $pythonVersion = "3"
    }

    #Install-Deps-Linux

    if (Test-Path "/etc/os-release") {
        $distro = (Get-Linux-Distro-Name)
        $versionId = (Get-Linux-Distro-Version)
        
        try {
            switch ($distro) {
                "debian" {
                    Invoke-BashCommand -Command "sudo apt-get update -y"
                    Invoke-BashCommand -Command "sudo apt-get install -y tk tcl libpython$pythonVersion-dev python$pythonVersion python$pythonVersion-dev python$pythonVersion-venv python$pythonVersion-pip"
                    break
                }
                "ubuntu" {
                    Invoke-BashCommand -Command "sudo apt-get update -y"
                    Invoke-BashCommand -Command "sudo apt-get install -y tk tcl libpython$pythonVersion-dev python$pythonVersion python$pythonVersion-dev python$pythonVersion-venv python$pythonVersion-pip"
                    break
                }
                "alpine" {
                    if ($pythonVersion -eq "3") {
                        Invoke-BashCommand -Command "sudo apk update"
                        Invoke-BashCommand -Command "sudo apk add --update --no-cache tk-dev tcl-dev tcl tk python$pythonVersion python$pythonVersion-tkinter"
    
                        # Check if /usr/local/bin/python3 already exists and create or overwrite the symlink based on that
                        Invoke-BashCommand -Command "
                        if [ ! -f /usr/local/bin/python3 ]; then
                            sudo ln -sf /usr/bin/python$pythonVersion /usr/local/bin/python3
                        fi
                        sudo ln -sf /usr/bin/python$pythonVersion /usr/local/bin/python$pythonVersion
                        "
                        Invoke-BashCommand -Command "/usr/local/bin/python$pythonVersion -m ensurepip"
                        Invoke-BashCommand -Command "/usr/local/bin/python$pythonVersion -m pip install --no-cache --upgrade pip setuptools"
                    } else {
                        throw "Python version $pythonVersion cannot be installed from package manager on Alpine."
                    }
                    break
                }
                "almalinux" {
                    Invoke-BashCommand -Command "sudo dnf update -y"
                    #Invoke-BashCommand -Command "sudo dnf upgrade -y"
                    Invoke-BashCommand -Command "sudo dnf install python$pythonVersion python$pythonVersion tk tcl tk-devel tcl-devel -y"
                    break
                }
                "fedora" {
                    Invoke-BashCommand -Command "sudo dnf update -y"
                    #Invoke-BashCommand -Command "sudo dnf upgrade -y"
                    Invoke-BashCommand -Command "sudo dnf install python$pythonVersion python$pythonVersion tk tcl tk-devel tcl-devel dnf-plugins-core -y"
                    break
                }
                "centos" {
                    Invoke-BashCommand -Command "sudo yum update -y"
                    if ( $versionId -eq "7" ) {
                        Invoke-BashCommand -Command "sudo yum install epel-release -y"
                    }
                    #Invoke-BashCommand -Command "sudo dnf upgrade -y"
                    Invoke-BashCommand -Command "sudo yum install python$pythonVersion python$pythonVersion tk tcl tk-devel tcl-devel -y"
                    break
                }
                "arch" {
                    Write-Host "Initializing pacman keyring..."
                    Invoke-BashCommand -Command "sudo pacman-key --init"
                    Invoke-BashCommand -Command "sudo pacman-key --populate archlinux"
                    Invoke-BashCommand -Command "sudo pacman -Sy archlinux-keyring --noconfirm"
                    if ($pythonVersion -eq "3") {
                        Invoke-BashCommand -Command "sudo pacman -Sy --noconfirm"
                        Invoke-BashCommand -Command "sudo pacman -Sy base-devel python-pip python tk tcl --noconfirm"
                    } else {
                        throw "Package manager does not support version '$pythonVersion' on arch."
                    }
                }
                default {
                    Write-Error "Unsupported Linux distribution for package manager install of Python: $distro"
                }
            }
            Find-Python -installIfNotFound $false
            if ( -not $global:pythonInstallPath ) {
                throw "Python not found/installed"
            }
        } catch {
            $errMsg = $_.Exception.Message
            Handle-Error -ErrorRecord $_
            $errStr = "Error: $errMsg`nCould not install python from your package manager`n`nWould you like to attempt to build from source instead? (y/N)"
            if ($noprompt) {
                Write-Host $errStr
                $userInput = "y"
                Write-Host $userInput
            } else {
                $userInput = Read-Host $errStr
            }
            if ( $userInput -ne "Y" -and $userInput -ne "y" ) {
                Write-Host "Press any key to exit..."
                $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
                exit 1
            }

            # Fallback mechanism for each distribution
            Install-TclTk  # TODO(th3w1zard1): move this up and separate tk/tcl package manager installs from python. Tk/tcl needs to be installed first.
            switch ($distro) {
                "debian" {
                    Invoke-BashCommand -Command 'sudo apt-get update -y'
                    Invoke-BashCommand -Command 'sudo apt-get install -y tk tcl build-essential zlib1g-dev libncurses5-dev libgdbm-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev libbz2-dev tk-dev'
                }
                "ubuntu" {
                    Invoke-BashCommand -Command 'sudo apt-get update -y'
                    Invoke-BashCommand -Command 'sudo apt-get install -y tk tcl build-essential zlib1g-dev libncurses5-dev libgdbm-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev libbz2-dev tk-dev'
                }
                "alpine" {
                    Invoke-BashCommand -Command 'sudo apk add --update --no-cache tk tcl tk-dev tcl-dev alpine-sdk linux-headers zlib-dev bzip2-dev readline-dev sqlite-dev openssl-dev libffi-dev'
                }
                "fedora" {
                    Invoke-BashCommand -Command 'sudo dnf groupinstall "Development Tools" -y'
                    Invoke-BashCommand -Command 'sudo dnf install -y tk tcl tk-devel dnf-plugins-core tcl-devel zlib-devel bzip2-devel readline-devel sqlite-devel openssl-devel libffi-devel'
                }
                "almalinux" {
                    Invoke-BashCommand -Command 'sudo yum groupinstall "Development Tools" -y'
                    Invoke-BashCommand -Command 'sudo yum install -y tk tcl tk-devel tcl-devel zlib-devel bzip2-devel readline-devel sqlite-devel openssl-devel libffi-devel'
                    Invoke-BashCommand -Command "gcc --version"
                }
                "centos" {
                    Invoke-BashCommand -Command 'sudo yum groupinstall "Development Tools" -y'
                    Invoke-BashCommand -Command 'sudo yum install -y tk tcl tk-devel tcl-devel zlib-devel bzip2-devel readline-devel sqlite-devel openssl-devel libffi-devel'
                    Invoke-BashCommand -Command "gcc --version"
                } default {
                    # Check for the presence of package managers and execute corresponding commands
                    if (Get-Command apt-get -ErrorAction SilentlyContinue) {
                        Invoke-BashCommand -Command 'sudo apt-get update -y'
                        Invoke-BashCommand -Command 'sudo apt-get install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev libbz2-dev tk-dev tcl-dev tk tcl'
                    } elseif (Get-Command apk -ErrorAction SilentlyContinue) {
                        Invoke-BashCommand -Command 'sudo apk add --update --no-cache tcl tk tk-dev linux-headers zlib-dev bzip2-dev readline-dev sqlite-dev openssl-dev libffi-dev'
                    } elseif (Get-Command yum -ErrorAction SilentlyContinue) {
                        Invoke-BashCommand -Command 'sudo yum groupinstall "Development Tools" -y'
                        Invoke-BashCommand -Command 'sudo yum install -y tk tcl tk-devel tcl-devel zlib-devel bzip2-devel readline-devel sqlite-devel openssl-devel libffi-devel'
                    } elseif (Get-Command dnf -ErrorAction SilentlyContinue) {
                        Invoke-BashCommand -Command 'sudo dnf groupinstall "Development Tools" -y'
                        Invoke-BashCommand -Command 'sudo dnf install -y tk tcl tk-devel tcl-devel zlib-devel bzip2-devel readline-devel sqlite-devel openssl-devel libffi-devel'
                    } elseif (Get-Command zypper -ErrorAction SilentlyContinue) {
                        Invoke-BashCommand -Command 'sudo zypper install -t pattern devel_basis'
                        Invoke-BashCommand -Command 'sudo zypper install -y zlib-devel bzip2-devel readline-devel sqlite3-devel openssl-devel tk-devel tcl-devel libffi-devel'
                    } elseif (Get-Command pacman -ErrorAction SilentlyContinue) {
                        Invoke-BashCommand -Command 'sudo pacman -Sy base-devel zlib bzip2 readline sqlite openssl tk tcl libffi --noconfirm'
                    } elseif (Get-Command brew -ErrorAction SilentlyContinue) {
                        brew update
                        brew install zlib bzip2 readline sqlite openssl libffi tcl-tk
                    } elseif (Get-Command snap -ErrorAction SilentlyContinue) {
                        Write-Warning "Snap packages are not directly applicable for building Python. Please ensure build dependencies are installed using another package manager."
                    } elseif (Get-Command flatpak -ErrorAction SilentlyContinue) {
                        Write-Warning "Flatpak is not suitable for installing build dependencies. Please use another package manager."
                    } else {
                        Write-Warning "Compatible package manager not found. Please install the build dependencies manually."
                    }
                }
            }
            Install-PythonUnixSource -pythonVersion $pythonVersion
            Invoke-BashCommand -Command "python$pythonVersion --version"
        }
    } else {
        Write-Host "Cannot determine Linux distribution."
        exit 1
    }
}

function Install-Python-Mac {
    Param (
        [string]$pythonVersion  # MAJOR.MINOR!!!
    )

    $pyVersion = switch ($pythonVersion) {
        "3.7" { "3.7.9" }
        "3.8" { "3.8.10" }
        "3.9" { "3.9.13" }
        "3.10" { "3.10.11" }
        "3.11" { "3.11.8" }
        "3.12" { "3.12.2" }
        "3.13" { "3.13.0a5" }
        default { throw "Unsupported Python version: $pythonVersion" }
    }
    
    # Map of Python versions to their detailed installer information
    $pythonInstallers = @{
        "3.7" = @("python-$pyVersion-macosx10.9.pkg")
        "3.8" = @("python-$pyVersion-macos11.pkg", "python-$pyVersion-macosx10.9.pkg")
        "3.9" = @("python-$pyVersion-macos11.pkg", "python-$pyVersion-macosx10.9.pkg")
        "3.10" = @("python-$pyVersion-macos11.pkg")
        "3.11" = @("python-$pyVersion-macos11.pkg")
        "3.12" = @("python-$pyVersion-macos11.pkg")
        "3.13" = @("python-$pyVersion-macos11.pkg")
    }

    Install-TclTk

    try {
        # Retrieve current macOS version
        $macOSVersion = bash -c "sw_vers -productVersion"
        $majorMacOSVersion = [int]$macOSVersion.Split('.')[0]
        $minorMacOSVersion = [int]$macOSVersion.Split('.')[1]

        Write-Host "macOS version: $macOSVersion"
        Write-Host "macOS version major: $majorMacOSVersion"
        Write-Host "macOS version minor: $minorMacOSVersion"

        $installerSelection = $pythonInstallers[$pythonVersion] | Where-Object {
            $_ -match "macosx?($majorMacOSVersion)\.(\d+)" -or $_ -match "macos($majorMacOSVersion)"
        } | Sort-Object -Descending | Select-Object -First 1

        Write-Host "installer selection: $installerSelection"

        if (-not $installerSelection) {
            # Fallback to the highest available lower macOS version installer
            $installerSelection = $pythonInstallers[$pythonVersion] | Sort-Object -Descending | Select-Object -First 1
            Write-Warning "No matching macOS version installer found. Falling back to highest available version: $installerSelection"
        }

        $pythonInstallerUrl = "https://www.python.org/ftp/python/$pyVersion/$installerSelection"

        # Download the installer
        $installerPath = "$HOME/Downloads/$installerSelection"
        Invoke-WebRequest -Uri $pythonInstallerUrl -OutFile $installerPath
        Write-Host "Downloaded $installerSelection and ready for installation."
        # Execute the installer command with sudo
        Invoke-BashCommand "sudo installer -pkg $installerPath -target /"
    } catch {
        Handle-Error -ErrorRecord $_
        try {
            Install-PythonUnixSource -pythonVersion $pythonVersion
        } catch {
            Handle-Error -ErrorRecord $_
            Write-Host "Attempting to install via brew."
            brew install python@$pyVersion python-tk@$pyVersion
            return $true
        }
        return $false
    }
}

function Install-PythonUnixSource {
    Param (
        [string]$pythonVersion  # MAJOR.MINOR!!!
    )
    $pyVersion = switch ($pythonVersion) {
        "3.7" { "3.7.17" }
        "3.8" { "3.8.18" }
        "3.9" { "3.9.18" }
        "3.10" { "3.10.13" }
        "3.11" { "3.11.8" }
        "3.12" { "3.12.2" }
        "3.13" { "3.13.0a5" }
        default { throw "Unsupported Python version: $pythonVersion" }
    }

    $pythonSrcUrl = "https://www.python.org/ftp/python/$pyVersion/Python-$pyVersion.tgz"
    Write-Output "Downloading python $pyVersion from $pythonSrcUrl..."
    Invoke-WebRequest -Uri $pythonSrcUrl -OutFile Python-$pyVersion.tgz
    Invoke-BashCommand -Command "tar -xvf Python-$pyVersion.tgz"
    $current_working_dir = (Get-Location).Path
    Set-Location -LiteralPath "Python-$pyVersion" -ErrorAction Stop

    # Conditionally apply --disable-new-dtags based on platform
    $configureOptions = "--enable-optimizations --with-ensurepip=install --enable-shared"
    if ((Get-OS) -eq "Linux") {
        $configureOptions += ' LDFLAGS="-Wl,--disable-new-dtags"'
    }

    Invoke-BashCommand -Command "sudo ./configure $configureOptions"

    # Check platform and set command for parallel make
    $makeParallel = if ((Get-OS) -eq "Linux") { "$(Invoke-BashCommand -Command 'nproc')" } elseif ((Get-OS) -eq "Mac") { "$(Invoke-BashCommand -Command 'sysctl -n hw.ncpu')" } else { "1" }

    Invoke-BashCommand -Command "sudo make -j $makeParallel"
    # Do NOT use `make install`. `make altinstall` will install it system-wide, but not as the default system python. (e.g. /usr/local/bin/python3.8)
    # Using `make install` may break system packages, so we use `make altinstall` here.
    Invoke-BashCommand -Command "sudo make altinstall"
    Set-Location -LiteralPath $current_working_dir
    $global:pythonInstallPath = "/usr/local/bin/python$pythonVersion"
}

function RefreshEnvVar {
    Param (
        [string]$varName
    )
    if ((Get-OS) -eq "Windows") {
        $userPath = Get-ItemProperty -Path 'Registry::HKEY_CURRENT_USER\Environment' -Name $varName | Select-Object -ExpandProperty $varName
        $systemPath = Get-ItemProperty -Path 'Registry::HKEY_LOCAL_MACHINE\System\CurrentControlSet\Control\Session Manager\Environment' -Name $varName | Select-Object -ExpandProperty $varName
    } else {  # FIXME(th3w1zard1): [System.Environment]::GetEnvironmentVariable only takes the session's env variable, we need to source .bashrc or whatever for linux/mac to truly update.
        $userPath = [System.Environment]::GetEnvironmentVariable($varName, [System.EnvironmentVariableTarget]::User)
        $systemPath = [System.Environment]::GetEnvironmentVariable($varName, [System.EnvironmentVariableTarget]::Machine)
    }
    Set-Item -Path $envVarName -Value ($userPath + ";" + $systemPath)
}

function Install-PythonWindows {
    Param (
        [string]$pythonVersion  # MAJOR.MINOR!!!
    )
    $pyVersion = switch ($pythonVersion) {
        "3.7" { "3.7.9" }
        "3.8" { "3.8.10" }
        "3.9" { "3.9.13" }
        "3.10" { "3.10.11" }
        "3.11" { "3.11.8" }
        "3.12" { "3.12.2" }
        default { throw "Unsupported Python version: $pythonVersion" }
    }
    # Check if running on GitHub Actions
    if ($env:GITHUB_ACTIONS -eq "true") {
        Write-Host "Running on GitHub Actions."
        $runnerArch = $env:MATRIX_ARCH
        Write-Host "Runner architecture is $runnerArch."
        $installerName = switch ($runnerArch) {
            "x86" { "python-$pyVersion.exe" }
            "x64" { "python-$pyVersion-amd64.exe" }
            default { throw "Unknown runner architecture: $runnerArch" }
        }
    }
    else {
        Write-Host "Not running on GitHub Actions."
        $installerName = if ([System.Environment]::Is64BitOperatingSystem) {
            "python-$pyVersion-amd64.exe"
        } else {
            "python-$pyVersion.exe"
        }
    }

    try {
        # Download and install Python
        $pythonInstallerUrl = "https://www.python.org/ftp/python/$pyVersion/$installerName"
        $installerPath = "$env:TEMP/$installerName"
        $curPath = Get-Location
        $logPath = "$curPath/PythonInstall.log"
        Write-Host "Downloading '$installerName' to '$env:TEMP', please wait..."
        Invoke-WebRequest -Uri $pythonInstallerUrl -OutFile $installerPath
        Write-Host "Download completed."
        Write-Host "Installing '$installerName', please wait..."
        Start-Process -FilePath $installerPath -Args "/quiet /log $logPath InstallAllUsers=0 PrependPath=1 InstallLauncherAllUsers=0" -Wait -NoNewWindow
        Write-Host "Python install process has finished."
        Get-Content -Path $logPath | ForEach-Object { Write-Host $_ }
    
        Write-Host "Refresh environment variables to detect new Python installation"
        $systemPath = Get-ItemProperty -Path 'Registry::HKEY_LOCAL_MACHINE\System\CurrentControlSet\Control\Session Manager\Environment' -Name PATH | Select-Object -ExpandProperty PATH
        $userPath = Get-ItemProperty -Path 'Registry::HKEY_CURRENT_USER\Environment' -Name PATH | Select-Object -ExpandProperty PATH
        $env:Path = $userPath + ";" + $systemPath
        Write-Debug "New PATH env: $env:PATH"
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
            $pythonVersionOutput = & $pythonPath --version 2>&1
            $pythonVersionString = $pythonVersionOutput -replace '^Python\s+'
            $numericVersionString = $pythonVersionString -replace '(\d+\.\d+\.\d+).*', '$1'
            $pythonVersion = [Version]$numericVersionString
            return $pythonVersion
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
    $pythonVersion = Get-Python-Version $pythonPath

    if ($pythonVersion -ge $minVersion -and $pythonVersion -le $lessThanVersion) {
        Write-Host "Python $pythonVersion install detected."
    } elseif ($pythonVersion -ge $minVersion) {
        Write-Warning "The Python version on PATH ($pythonVersion) is not fully tested, please consider using python 3.8. Continuing anyway..."
    } else {
        Write-Error "Your installed Python version '$pythonVersion' is not supported. Please install a python version between '$minVersion' and '$maxVersion'"
        Write-Host "Press any key to exit..."
        if (-not $noprompt) {
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        }
        exit
    }

    return [PSCustomObject]@{
        Version = $pythonVersion
        Path = $pythonPath
    }
}

function Get-PythonPaths {
    Param (
        [string]$version
    )

    $windowsVersion = $version -replace '\.', ''  # "3.8" becomes "38"

    $windowsPaths = @(
        "C:\Program Files\Python$windowsVersion\python.exe",
        "$env:ProgramFiles\Python$windowsVersion\python.exe",
        "C:\Program Files (x86)\Python$windowsVersion\python.exe",
        "$env:ProgramFiles(x86)\Python$windowsVersion\python.exe"
        "C:\Program Files\Python$windowsVersion-32\python.exe",
        "C:\Program Files (x86)\Python$windowsVersion-32\python.exe",
        "$env:USERPROFILE\AppData\Local\Programs\Python\Python$windowsVersion\python.exe",
        "$env:USERPROFILE\AppData\Local\Programs\Python\Python$windowsVersion-32\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python$windowsVersion-64\python.exe",
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

function Test-PythonCommand {
    param (
        [string]$CommandName
    )
    $pythonCommand = Get-Command -Name $CommandName -ErrorAction SilentlyContinue
    if ($null -ne $pythonCommand) {
        $testPath = Get-Path-From-Command $CommandName
        $global:pythonVersion = Get-Python-Version $testPath
        if ($global:pythonVersion -ge $minVersion -and $global:pythonVersion -lt $maxVersion) {
            Write-Host "Found python command with version $global:pythonVersion at path $testPath"
            $global:pythonInstallPath = $testPath
            return $true
        } else {
            Write-Host "python '$testPath' version '$global:pythonVersion' not supported"
            $global:pythonInstallPath = ""
            $global:pythonVersion = ""
        }
    }
    return $false
}

function Find-Python {
    Param (
        [bool]$installIfNotFound
    )
    if ($global:pythonInstallPath) {
        $testVersion = Get-Python-Version -pythonPath $global:pythonInstallPath
        if ($testVersion -ne [Version]"0.0.0") {
            $global:pythonVersion = Get-Python-Version $global:pythonInstallPath
            if ($global:pythonVersion -ge $minVersion -and $global:pythonVersion -lt $maxVersion) {
                Write-Host "Found python command with version $global:pythonVersion at path $global:pythonInstallPath"
                return
            }
        }
    }

    # Check for Python 3 command and version
    if ($global:force_python_version) {
        $fallbackVersion = $global:force_python_version
        Write-Host "Fallback version: $fallbackVersion"
        $pythonVersions = @("python$fallbackVersion")
    } else {
        $fallbackVersion = "{0}.{1}" -f $recommendedVersion.Major, $recommendedVersion.Minor
        $pythonVersions = @('python3.8', 'python3', 'python3.9', 'python3.10', 'python3.11', 'python3.12', 'python3.13', 'python3.14', 'python')
    }
    foreach ($pyCommandPathCheck in $pythonVersions) {
        if (Test-PythonCommand -CommandName $pyCommandPathCheck) {
            break
        }
    }

    if ( -not $global:pythonInstallPath -or ($global:pythonVersion -and $global:pythonVersion -ge $recommendedVersion) ) {
        Write-Host "Check 1 pass"
        foreach ($version in $pythonVersions) {
            $version = $version -replace "python", ""
            $paths = (Get-PythonPaths $version)[(Get-OS)]
            foreach ($path in $paths) {
                try {
                    # Resolve potential environment variables in the path
                    $resolvedPath = [Environment]::ExpandEnvironmentVariables($path)
                    Write-Host "Check 2: $resolvedPath"
                    if (Test-Path $resolvedPath -ErrorAction SilentlyContinue) {
                        Write-Host "Check 3: $resolvedPath exists!"
                        $thisVersion = Get-Python-Version $resolvedPath
                        if ($thisVersion -ge $minVersion -and $thisVersion -le $maxVersion) {
                            Write-Host "Check 4: $resolvedPath has $thisVersion which matches our version range."
                            # Valid path or better recommended path found.
                            if (-not $global:pythonInstallPath -or $thisVersion -le $recommendedVersion) {
                                Write-Host "Found better python install path with version $thisVersion at path '$resolvedPath'"
                                $global:pythonInstallPath = $resolvedPath
                                $global:pythonVersion = $thisVersion
                            }

                            # HACK: to prevent ubuntu/debian reinstalls
                            if ($resolvedPath.StartsWith("/usr/local/bin/python") -and ((Get-Linux-Distro-Name) -eq "debian" -or (Get-Linux-Distro-Name) -eq "ubuntu")) {
                                Write-Host "altinstall detected with version $thisVersion at path '$resolvedPath', not running custom install hook."
                                $global:pythonInstallPath = $resolvedPath
                                $global:pythonVersion = $thisVersion
                                return
                            }
                        }
                    }
                } catch {
                    Handle-Error -ErrorRecord $_
                }
            }
        }
    }
    
    # Even if python is installed, debian-based distros need python3-venv packages and a few others.
    # Example: while a venv can be partially created, the 
    # partial won't create stuff like the activation scripts (so they need sudo apt-get install python3-venv)
    # they'll also be missing things like pip. This step fixes that.
    if ($installIfNotFound -and ((Get-Linux-Distro-Name) -eq "debian" -or (Get-Linux-Distro-Name) -eq "ubuntu")) {
        try {
            $versionTypeObj = New-Object -TypeName "System.Version" $global:pythonVersion
        } catch {
            $versionTypeObj = New-Object -TypeName "System.Version" $fallbackVersion
        }
        $shortVersion = "{0}.{1}" -f $versionTypeObj.Major, $versionTypeObj.Minor
        Install-Python-Linux -pythonVersion $shortVersion
    }

    if ( -not $global:pythonInstallPath ) {
        if ($installIfNotFound) {
            if (-not $noprompt) {
                $displayVersion = $global:force_python_version
                if (-not $displayVersion) {
                    $displayVersion = $recommendedVersion
                }
                Write-Host "A supported Python version was not detected on your system. Install Python version $displayVersion now automatically?"
                $userInput = Read-Host "(Y/N)"
                if ( $userInput -ne "Y" -and $userInput -ne "y" ) {
                    Write-Host "A python install between versions $minVersion and $maxVersion is required for PyKotor."
                    Write-Host "Press any key to exit..."
                    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
                    exit
                }
            }
            try {
                if ( (Get-OS) -eq "Windows" ) {
                    Install-PythonWindows -pythonVersion $fallbackVersion
                } elseif ( (Get-OS) -eq "Linux" ) {  # use $global:force_python_version, don't use $fallbackVersion for linux.
                    Install-Python-Linux -pythonVersion $global:force_python_version
                } elseif ( (Get-OS) -eq "Mac" ) {
                    Install-Python-Mac -pythonVersion $fallbackVersion
                }
            } catch {
                Handle-Error -ErrorRecord $_
                Write-Host "The Python install either failed or has been cancelled."
                Write-Host "A python install between versions $minVersion and $maxVersion is required for PyKotor."
                Write-Host "Press any key to exit..."
                $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
                exit
            }
            Write-Host "Find python again now that it's been installed."
            Find-Python -installIfNotFound $false
        }
    }
}

# (This check is disabled - this should already happen when activating a new venv)
# Check if the 'deactivate' function already exists
# if (-not (Get-Command -Name 'deactivate' -CommandType Function -ErrorAction SilentlyContinue)) {

<#
.SYNOPSIS
Fallback deactivate function

.DESCRIPTION
Sometimes the deactivate function isn't found for whatever reason. This definition ensures it can always be used.

.Parameter NonDestructive
If present, do not remove this function from the global namespace for the session.

.NOTES
This function will ALWAYS be overridden by the activation script.
#>
function global:deactivate ([switch]$NonDestructive) {
    # Revert to original values

    # The prior prompt:
    if (Test-Path -Path Function:_OLD_VIRTUAL_PROMPT) {
        Copy-Item -Path Function:_OLD_VIRTUAL_PROMPT -Destination Function:prompt
        Remove-Item -Path Function:_OLD_VIRTUAL_PROMPT
    }

    # The prior PYTHONHOME:
    if (Test-Path -Path Env:_OLD_VIRTUAL_PYTHONHOME) {
        Copy-Item -Path Env:_OLD_VIRTUAL_PYTHONHOME -Destination Env:PYTHONHOME
        Remove-Item -Path Env:_OLD_VIRTUAL_PYTHONHOME
    }

    # The prior PATH:
    if (Test-Path -Path Env:_OLD_VIRTUAL_PATH) {
        Copy-Item -Path Env:_OLD_VIRTUAL_PATH -Destination Env:PATH
        Remove-Item -Path Env:_OLD_VIRTUAL_PATH
    }

    # Just remove the VIRTUAL_ENV altogether:
    if (Test-Path -Path Env:VIRTUAL_ENV) {
        Remove-Item -Path env:VIRTUAL_ENV
    }

    # Just remove VIRTUAL_ENV_PROMPT altogether.
    if (Test-Path -Path Env:VIRTUAL_ENV_PROMPT) {
        Remove-Item -Path env:VIRTUAL_ENV_PROMPT
    }

    # Just remove the _PYTHON_VENV_PROMPT_PREFIX altogether:
    if (Get-Variable -Name "_PYTHON_VENV_PROMPT_PREFIX" -ErrorAction SilentlyContinue) {
        Remove-Variable -Name _PYTHON_VENV_PROMPT_PREFIX -Scope Global -Force
    }

    # Leave deactivate function in the global namespace if requested:
    if (-not $NonDestructive) {
        Remove-Item -Path function:deactivate
    }
}

$venvPath = $repoRootPath + $pathSep + $venv_name
$findVenvExecutable = $true
$installPipToVenvManually = $false
if (Get-ChildItem Env:VIRTUAL_ENV -ErrorAction SilentlyContinue) {  # Check if a venv is already activated
    $venvPath = $env:VIRTUAL_ENV
    Write-Host "A currently activated virtual environment found: $venvPath"
    deactivate
} elseif ($venvPath -ne ($repoRootPath + $pathSep) -and (Test-Path $venvPath -ErrorAction SilentlyContinue)) {
    Write-Host "Found non-activated existing python virtual environment at '$venvPath'"
} else {
    Find-Python -installIfNotFound $true
    if ( -not $global:pythonInstallPath ) {
        if ( -not $noprompt ) {
            Write-Warning "Could not find path to python. Try again?"
            $userInput = Read-Host "(Y/N)"
            if ( $userInput -ne "Y" -and $userInput -ne "y" ) {
                $userInput = Read-Host "Enter the path to python executable:"
                if ( Test-Path -LiteralPath $userInput -ErrorAction SilentlyContinue ) {
                    $global:pythonInstallPath = $userInput
                } else {
                    Write-Error "Python executable not found at '$userInput'"
                    Write-Host "Press any key to exit..."
                    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
                    exit
                }
            } else {
                Find-Python -installIfNotFound $true
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
        Write-Error "Failed to create virtual environment. Ensure Python is installed correctly."
        Write-Warning "Attempt to use main python install at $global:pythonInstallPath instead of a venv? (not recommended)"
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
        if ((Get-OS) -ne "Windows") {

            $activateScriptBash = Join-Path -Path $venvPath -ChildPath "bin/activate"
            $activateScriptPs1 = Join-Path -Path $venvPath -ChildPath "bin/Activate.ps1"
    
            # Check if activate scripts are created
            # The below code fixes a bug on a specific linux distro. I cannot remember which distro, I wish I documented it, and the issue thread this was inspired by.
            # Could be ubuntu without `sudo apt-get install python3-pip python3-venv`, but I don't believe it was that specific case.
            if (-not (Test-Path $activateScriptPs1) -and -not (Test-Path $activateScriptBash)) {
                Write-Warning "Neither activate nor Activate.ps1 scripts were found. Deleting the virtual environment and attempting to recreate it with --without-pip..."
                Remove-Item -LiteralPath $venvPath -Recurse -Force
                & $global:pythonInstallPath -m venv --without-pip $venvPath 2>&1
                $installPipToVenvManually = $true
    
                Write-Warning "Virtual environment recreated without pip. Will install pip in a later step."
            } else {
                Write-Host "Virtual environment created and activate scripts found."
            }
        }
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


# Sometimes a system may be missing activation scripts...
$activateBashScriptContents = @"
# This file must be used with "source bin/activate" *from bash*
# You cannot run it directly

deactivate () {
# reset old environment variables
if [ -n "`${_OLD_VIRTUAL_PATH:-}" ] ; then
PATH="`${_OLD_VIRTUAL_PATH:-}"
export PATH
unset _OLD_VIRTUAL_PATH
fi
if [ -n "`${_OLD_VIRTUAL_PYTHONHOME:-}" ] ; then
PYTHONHOME="`${_OLD_VIRTUAL_PYTHONHOME:-}"
export PYTHONHOME
unset _OLD_VIRTUAL_PYTHONHOME
fi

# Call hash to forget past commands. Without forgetting
# past commands the `$PATH changes we made may not be respected
hash -r 2> /dev/null

if [ -n "`${_OLD_VIRTUAL_PS1:-}" ] ; then
PS1="`${_OLD_VIRTUAL_PS1:-}"
export PS1
unset _OLD_VIRTUAL_PS1
fi

unset VIRTUAL_ENV
unset VIRTUAL_ENV_PROMPT
if [ ! "`${1:-}" = "nondestructive" ] ; then
# Self destruct!
unset -f deactivate
fi
}

# unset irrelevant variables
deactivate nondestructive

# on Windows, a path can contain colons and backslashes and has to be converted:
if [ "`$OSTYPE" = "cygwin" ] || [ "`$OSTYPE" = "msys" ] ; then
# transform D:\path\to\venv to /d/path/to/venv on MSYS
# and to /cygdrive/d/path/to/venv on Cygwin
export VIRTUAL_ENV=`$(cygpath "$venvScriptBinPath")
else
# use the path as-is
export VIRTUAL_ENV="$venvScriptBinPath"
fi

_OLD_VIRTUAL_PATH="`$PATH"
PATH="`$VIRTUAL_ENV/bin:`$PATH"
export PATH

# unset PYTHONHOME if set
# this will fail if PYTHONHOME is set to the empty string (which is bad anyway)
# could use `if (set -u; : `$PYTHONHOME) ;` in bash
if [ -n "`${PYTHONHOME:-}" ] ; then
_OLD_VIRTUAL_PYTHONHOME="`${PYTHONHOME:-}"
unset PYTHONHOME
fi

if [ -z "`${VIRTUAL_ENV_DISABLE_PROMPT:-}" ] ; then
_OLD_VIRTUAL_PS1="`${PS1:-}"
PS1="($venv_name) `${PS1:-}"
export PS1
VIRTUAL_ENV_PROMPT="($venv_name) "
export VIRTUAL_ENV_PROMPT
fi

# Call hash to forget past commands. Without forgetting
# past commands the `$PATH changes we made may not be respected
hash -r 2> /dev/null"@

$activatePwshScriptContents = @"
<#
.Synopsis
Activate a Python virtual environment for the current PowerShell session.

.Description
Pushes the python executable for a virtual environment to the front of the
`$Env:PATH environment variable and sets the prompt to signify that you are
in a Python virtual environment. Makes use of the command line switches as
well as the `pyvenv.cfg` file values present in the virtual environment.

.Parameter VenvDir
Path to the directory that contains the virtual environment to activate. The
default value for this is the parent of the directory that the Activate.ps1
script is located within.

.Parameter Prompt
The prompt prefix to display when this virtual environment is activated. By
default, this prompt is the name of the virtual environment folder (VenvDir)
surrounded by parentheses and followed by a single space (ie. '(.venv) ').

.Example
Activate.ps1
Activates the Python virtual environment that contains the Activate.ps1 script.

.Example
Activate.ps1 -Verbose
Activates the Python virtual environment that contains the Activate.ps1 script,
and shows extra information about the activation as it executes.

.Example
Activate.ps1 -VenvDir C:\Users\MyUser\Common\.venv
Activates the Python virtual environment located in the specified location.

.Example
Activate.ps1 -Prompt "MyPython"
Activates the Python virtual environment that contains the Activate.ps1 script,
and prefixes the current prompt with the specified string (surrounded in
parentheses) while the virtual environment is active.

.Notes
On Windows, it may be required to enable this Activate.ps1 script by setting the
execution policy for the user. You can do this by issuing the following PowerShell
command:

PS C:\> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

For more information on Execution Policies: 
https://go.microsoft.com/fwlink/?LinkID=135170

#>
Param(
[Parameter(Mandatory = $false)]
[String]
`$VenvDir,
[Parameter(Mandatory = $false)]
[String]
`$Prompt
)

<# Function declarations --------------------------------------------------- #>

<#
.Synopsis
Remove all shell session elements added by the Activate script, including the
addition of the virtual environment's Python executable from the beginning of
the PATH variable.

.Parameter NonDestructive
If present, do not remove this function from the global namespace for the
session.

#>
function global:deactivate ([switch]`$NonDestructive) {
# Revert to original values

# The prior prompt:
if (Test-Path -Path Function:_OLD_VIRTUAL_PROMPT) {
Copy-Item -Path Function:_OLD_VIRTUAL_PROMPT -Destination Function:prompt
Remove-Item -Path Function:_OLD_VIRTUAL_PROMPT
}

# The prior PYTHONHOME:
if (Test-Path -Path Env:_OLD_VIRTUAL_PYTHONHOME) {
Copy-Item -Path Env:_OLD_VIRTUAL_PYTHONHOME -Destination Env:PYTHONHOME
Remove-Item -Path Env:_OLD_VIRTUAL_PYTHONHOME
}

# The prior PATH:
if (Test-Path -Path Env:_OLD_VIRTUAL_PATH) {
Copy-Item -Path Env:_OLD_VIRTUAL_PATH -Destination Env:PATH
Remove-Item -Path Env:_OLD_VIRTUAL_PATH
}

# Just remove the VIRTUAL_ENV altogether:
if (Test-Path -Path Env:VIRTUAL_ENV) {
Remove-Item -Path env:VIRTUAL_ENV
}

# Just remove the _PYTHON_VENV_PROMPT_PREFIX altogether:
if (Get-Variable -Name "_PYTHON_VENV_PROMPT_PREFIX" -ErrorAction SilentlyContinue) {
Remove-Variable -Name _PYTHON_VENV_PROMPT_PREFIX -Scope Global -Force
}

# Leave deactivate function in the global namespace if requested:
if (-not `$NonDestructive) {
Remove-Item -Path function:deactivate
}
}

<#
.Description
Get-PyVenvConfig parses the values from the pyvenv.cfg file located in the
given folder, and returns them in a map.

For each line in the pyvenv.cfg file, if that line can be parsed into exactly
two strings separated by `=` (with any amount of whitespace surrounding the =)
then it is considered a `key = value` line. The left hand string is the key,
the right hand is the value.

If the value starts with a `'` or a `"` then the first and last character is
stripped from the value before being captured.

.Parameter ConfigDir
Path to the directory that contains the `pyvenv.cfg` file.
#>
function Get-PyVenvConfig(
[String]
`$ConfigDir
) {
Write-Verbose "Given ConfigDir=`$ConfigDir, obtain values in pyvenv.cfg"

# Ensure the file exists, and issue a warning if it doesn't (but still allow the function to continue).
`$pyvenvConfigPath = Join-Path -Resolve -Path `$ConfigDir -ChildPath 'pyvenv.cfg' -ErrorAction Continue

# An empty map will be returned if no config file is found.
`$pyvenvConfig = @{ }

if (`$pyvenvConfigPath) {

Write-Verbose "File exists, parse `key = value` lines"
`$pyvenvConfigContent = Get-Content -Path `$pyvenvConfigPath

`$pyvenvConfigContent | ForEach-Object {
`$keyval = `$PSItem -split "\s*=\s*", 2
if (`$keyval[0] -and `$keyval[1]) {
    `$val = `$keyval[1]

    # Remove extraneous quotations around a string value.
    if ("'""".Contains(`$val.Substring(0, 1))) {
        `$val = `$val.Substring(1, `$val.Length - 2)
    }

    `$pyvenvConfig[`$keyval[0]] = `$val
    Write-Verbose "Adding Key: '`$(`$keyval[0])'='`$val'"
}
}
}
return `$pyvenvConfig
}


<# Begin Activate script --------------------------------------------------- #>

# Determine the containing directory of this script
`$VenvExecPath = Split-Path -Parent `$MyInvocation.MyCommand.Definition
`$VenvExecDir = Get-Item -Path `$VenvExecPath

Write-Verbose "Activation script is located in path: '`$VenvExecPath'"
Write-Verbose "VenvExecDir Fullname: '`$(`$VenvExecDir.FullName)"
Write-Verbose "VenvExecDir Name: '`$(`$VenvExecDir.Name)"

# Set values required in priority: CmdLine, ConfigFile, Default
# First, get the location of the virtual environment, it might not be
# VenvExecDir if specified on the command line.
if (`$VenvDir) {
Write-Verbose "VenvDir given as parameter, using '`$VenvDir' to determine values"
}
else {
Write-Verbose "VenvDir not given as a parameter, using parent directory name as VenvDir."
`$VenvDir = `$VenvExecDir.Parent.FullName.TrimEnd("\\/")
Write-Verbose "VenvDir=`$VenvDir"
}

# Next, read the `pyvenv.cfg` file to determine any required value such
# as `prompt`.
`$pyvenvCfg = Get-PyVenvConfig -ConfigDir `$VenvDir

# Next, set the prompt from the command line, or the config file, or
# just use the name of the virtual environment folder.
if (`$Prompt) {
Write-Verbose "Prompt specified as argument, using '`$Prompt'"
}
else {
Write-Verbose "Prompt not specified as argument to script, checking pyvenv.cfg value"
if (`$pyvenvCfg -and `$pyvenvCfg['prompt']) {
Write-Verbose "  Setting based on value in pyvenv.cfg='`$(`$pyvenvCfg['prompt'])'"
`$Prompt = `$pyvenvCfg['prompt'];
}
else {
Write-Verbose "  Setting prompt based on parent's directory's name. (Is the directory name passed to venv module when creating the virutal environment)"
Write-Verbose "  Got leaf-name of `$VenvDir='`$(Split-Path -Path `$venvDir -Leaf)'"
`$Prompt = Split-Path -Path `$venvDir -Leaf
}
}

Write-Verbose "Prompt = '`$Prompt'"
Write-Verbose "VenvDir='`$VenvDir'"

# Deactivate any currently active virtual environment, but leave the
# deactivate function in place.
deactivate -nondestructive

# Now set the environment variable VIRTUAL_ENV, used by many tools to determine
# that there is an activated venv.
`$env:VIRTUAL_ENV = `$VenvDir

if (-not `$Env:VIRTUAL_ENV_DISABLE_PROMPT) {

Write-Verbose "Setting prompt to '`$Prompt'"

# Set the prompt to include the env name
# Make sure _OLD_VIRTUAL_PROMPT is global
function global:_OLD_VIRTUAL_PROMPT { "" }
Copy-Item -Path function:prompt -Destination function:_OLD_VIRTUAL_PROMPT
New-Variable -Name _PYTHON_VENV_PROMPT_PREFIX -Description "Python virtual environment prompt prefix" -Scope Global -Option ReadOnly -Visibility Public -Value `$Prompt

function global:prompt {
Write-Host -NoNewline -ForegroundColor Green "(`$_PYTHON_VENV_PROMPT_PREFIX) "
_OLD_VIRTUAL_PROMPT
}
}

# Clear PYTHONHOME
if (Test-Path -Path Env:PYTHONHOME) {
Copy-Item -Path Env:PYTHONHOME -Destination Env:_OLD_VIRTUAL_PYTHONHOME
Remove-Item -Path Env:PYTHONHOME
}

# Add the venv to the PATH
Copy-Item -Path Env:PATH -Destination Env:_OLD_VIRTUAL_PATH
`$Env:PATH = "`$VenvExecDir`$([System.IO.Path]::PathSeparator)`$Env:PATH"
"@

function Activate-Script {
    param (
        [string]$scriptPath
    )
    try {
        & $scriptPath
        return $true
    } catch {
        Handle-Error -ErrorRecord $_
        return $false
    }
}

function Activate-PythonVenv {
    param (
        [Parameter(Mandatory=$true)]
        [string]$venvPath,
        [switch]$noRecurse
    )

    # Check if the venvPath exists
    if (-not (Test-Path -LiteralPath $venvPath)) {
        Write-Error "Virtual environment path '$venvPath' does not exist."
        return
    }

    Write-Host "Activating venv at '$venvPath'"
    if ((Get-OS) -eq "Windows") {
        $venvScriptBinPath = Join-Path -Path $venvPath -ChildPath "Scripts"
    } else {
        $venvScriptBinPath = Join-Path -Path $venvPath -ChildPath "bin"
    }
    try {
        $activateScriptPathPwsh = Join-Path -Path $venvScriptBinPath -ChildPath "Activate.ps1"
        $activateScriptPathBash = Join-Path -Path $venvScriptBinPath -ChildPath "activate"
        if (Test-Path $activateScriptPathPwsh) {
            if (-not (Activate-Script -scriptPath $activateScriptPathPwsh)) {
                if (Test-Path $activateScriptPathBash) {
                    Activate-Script -scriptPath $activateScriptPathBash
                } else {
                    throw "Bash script did not exist as a fallback."
                }
            }
        } elseif (Test-Path $activateScriptPathBash) {
            if (-not (Activate-Script -scriptPath $activateScriptPathBash)) {
                if (Test-Path $activateScriptPathPwsh) {
                    Activate-Script -scriptPath $activateScriptPathPwsh
                } else {
                    throw "PowerShell script did not exist as a fallback."
                }
            }
        } else {
            Write-Warning "venv activation script at '$activateScriptPath' did not exist, attempting to create activation scripts manually..."
            $activateBashScriptContents | Out-File -FilePath $activateScriptPathBash
            $activatePwshScriptContents | Out-File -FilePath $activateScriptPathPwsh
            if (-not $noRecurse) {
                Activate-PythonVenv -venvPath $venvPath -noRecurse
            }
        }
    } catch {
        Handle-Error -ErrorRecord $_
        Write-Error $_.Exception.Message
        Write-Error "venv activation script at '$activateScriptPath' failed."
    }
}

Activate-PythonVenv $venvPath

if ($installPipToVenvManually) {
    Write-Host "Installing pip to venv manually..."
    $originalLocation = Get-Location
    $tempPath = [System.IO.Path]::GetTempPath()
    try {
        # Download get-pip.py
        $getPipScriptPath = Join-Path -Path $tempPath -ChildPath "get-pip.py"
        Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $getPipScriptPath

        # Attempt to install pip
        & $pythonExePath $getPipScriptPath
        $pipPathUnix = Join-Path -Path $venvPath -ChildPath "bin/pip"
        if (-not $? -or (-not (Test-Path $pipPathUnix -ErrorAction SilentlyContinue))) {
            # Fallback to manual setuptools and pip installation
            Write-Error "Failed to install pip with get-pip.py, attempting fallback method..."

            Write-Host "Downloading/Installing setuptools-$latestSetuptoolsVersion"
            Invoke-WebRequest -Uri $latestSetuptoolsUrl -OutFile "setuptools-$latestSetuptoolsVersion.tar.gz"
            Invoke-BashCommand "tar -xzf `"setuptools-$latestSetuptoolsVersion.tar.gz`""
            Set-Location -LiteralPath "setuptools-$latestSetuptoolsVersion"
            & $pythonExePath setup.py install
            Set-Location -LiteralPath $originalLocation

            Write-Host "Downloading/Installing pip-$latestPipVersion"
            Invoke-WebRequest -Uri $latestPipPackageUrl -OutFile "pip-$latestPipVersion.tar.gz"
            Invoke-BashCommand -Command "tar -xzf `"pip-$latestPipVersion.tar.gz`""
            Set-Location -LiteralPath "pip-$latestPipVersion"
            & $pythonExePath setup.py install
            Set-Location -LiteralPath $originalLocation

            Activate-PythonVenv
        } else {
            Write-Host "pip installed successfully."
        }
    } finally {
        Set-Location -LiteralPath $originalLocation
    }
}

$pythonInfo = Initialize-Python $pythonExePath
Write-Host "`nInitialized Python Version: $($pythonInfo.Version)    Path: $($pythonInfo.Path)"
$pythonVersion = $pythonInfo.Version
$pythonExePath = $pythonInfo.Path

# Use Python to find the site-packages directory using sysconfig for compatibility with virtual environments
$sitePackagesPath = & $pythonExePath -c "import sysconfig; print(sysconfig.get_paths()['purelib'])"
Write-Host "`nSite-Packages Path: $sitePackagesPath"

# Set environment variables from .env file
$dotenv_path = "$repoRootPath$pathSep.env"
Write-Host "-----------------`nLoading project environment variables from '$dotenv_path':"
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
