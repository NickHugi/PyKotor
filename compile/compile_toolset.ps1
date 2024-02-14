param (
  [switch]$noprompt
)
$this_noprompt = $noprompt

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$rootPath = (Resolve-Path -LiteralPath "$scriptPath/..").Path
Write-Host "The path to the script directory is: $scriptPath"
Write-Host "The path to the root directory is: $rootPath"

Write-Host "Initializing python virtual environment..."
. $rootPath/install_python_venv.ps1

# Define temporary directories for build and cache
$tempBuildDir = "/tmp/pip_build/"
$tempCacheDir = "/tmp/pip_cache/"

# Ensure these temporary directories exist
Invoke-Expression "mkdir -p $tempBuildDir"
Invoke-Expression "mkdir -p $tempCacheDir"
$env:PIP_CACHE_DIR = $tempCacheDir

Write-Host "Installing required packages to build the holocron toolset..."
. $pythonExePath -m pip install --upgrade pip --prefer-binary --progress-bar on
. $pythonExePath -m pip install pyinstaller --prefer-binary --progress-bar on
. $pythonExePath -m pip install -r ($rootPath + $pathSep + "Tools" + $pathSep + "HolocronToolset" + $pathSep + "requirements.txt") --prefer-binary --compile --progress-bar on
. $pythonExePath -m pip install -r ($rootPath + $pathSep + "Libraries" + $pathSep + "PyKotor" + $pathSep + "requirements.txt") --prefer-binary --compile --progress-bar on
. $pythonExePath -m pip install -r ($rootPath + $pathSep + "Libraries" + $pathSep + "PyKotorGL" + $pathSep + "requirements.txt") --prefer-binary --compile --progress-bar on
. $pythonExePath -m pip install -r ($rootPath + $pathSep + "Libraries" + $pathSep + "PyKotorGL" + $pathSep + "recommended.txt") --prefer-binary --compile --progress-bar on

if ((Get-OS) -eq "Mac") {
    & "brew install python qt pyqt5 mpdecimal " +
               "` gstreamer gst-plugins-base gst-plugins-good gst-plugins-bad gst-plugins-ugly " +
               "` pulseaudio fontconfig"
} elseif (Test-Path -Path "/etc/os-release") {
    $osInfo = Get-Content "/etc/os-release" -Raw
    if ($osInfo -match 'ID=(.*)') {
        $distro = $Matches[1].Trim('"')
    }
    if ($osInfo -match 'VERSION_ID=(.*)') {
        $versionId = $Matches[1].Trim('"')
    }
    $command = ""
    switch ($distro) {
        "debian" {  # untested
            $command = "sudo apt install python3-opengl python3-pyqt5-sip python3-pyqt5 libpulse-mainloop-glib0 libgstreamer-plugins-base1.0-dev gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly libgstreamer1.0-dev mesa-utils libgl1-mesa-glx libgl1-mesa-dri qt5-default qtbase5-dev qtchooser qt5-qmake qtbase5-dev-tools libgl1-mesa-glx libglu1-mesa libglu1-mesa-dev libqt5gui5 libqt5core5a libqt5dbus5 libqt5widgets5 -y"
            break
        }
        "ubuntu" {  # export LIBGL_ALWAYS_SOFTWARE=1
            $command = "sudo apt install python3-opengl python3-pyqt5-sip python3-pyqt5 libpulse-mainloop-glib0 libgstreamer-plugins-base1.0-dev gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly libgstreamer1.0-dev mesa-utils libgl1-mesa-glx libgl1-mesa-dri qt5-default qtbase5-dev qtchooser qt5-qmake qtbase5-dev-tools libgl1-mesa-glx libglu1-mesa libglu1-mesa-dev libqt5gui5 libqt5core5a libqt5dbus5 libqt5widgets5 -y"
            break
        }
        "fedora" {
            $command = "sudo dnf install binutils python3-pyopengl PyQt5 pulseaudio-libs-glib2 gstreamer1-plugins-base gstreamer1-plugins-good gstreamer1-plugins-bad-free gstreamer1-plugins-ugly-free gstreamer1-devel -y"
            break
        }
        "almalinux" {
            $command = "sudo dnf install binutils libglvnd-opengl python3-qt5 python3-pyqt5-sip pulseaudio-libs-glib2 pulseaudio-libs-devel gstreamer1-plugins-base gstreamer1-plugins-good gstreamer1-plugins-bad-free mesa-libGLw libX11 mesa-dri-drivers mesa-libGL mesa-libglapi -y"
            break
        }
        "alpine" {  # export LIBGL_ALWAYS_SOFTWARE=1
            $command = "sudo apk add binutils gstreamer gstreamer-dev gst-plugins-bad-dev gst-plugins-base-dev pulseaudio-qt pulseaudio pulseaudio-alsa py3-opengl qt5-qtbase-x11 qt5-qtbase-dev mesa-gl mesa-glapi qt5-qtbase-x11 libx11 ttf-dejavu fontconfig"
            break
        }
        "arch" {
            $command = "sudo pacman -Syu --noconfirm && sudo pacman -S python-opengl mpdecimal python-pyqt5 qt5-base qt5-multimedia qt5-svg pulseaudio pulseaudio-alsa gstreamer mesa libglvnd ttf-dejavu fontconfig gst-plugins-base gst-plugins-good gst-plugins-bad gst-plugins-ugly --noconfirm"
            break
        }
    }

    if ($command -eq "") {
        Write-Warning "Dist $distro version $versionId not supported for automated system package install, please install the dependencies if you experience problems."
    } else {
        Write-Host "Executing command: $command"
        Invoke-Expression $command
    }
}

$current_working_dir = (Get-Location).Path
Set-Location -LiteralPath (Resolve-Path -LiteralPath "$rootPath/Tools/HolocronToolset/src").Path

# Determine the final executable path
$finalExecutablePath = $null
if ((Get-OS) -eq "Windows") {
    $finalExecutablePath = "$rootPath\dist\HolocronToolset.exe"
} elseif ((Get-OS) -eq "Linux") {
    $finalExecutablePath = "$rootPath/dist/HolocronToolset"
} elseif ((Get-OS) -eq "Mac") {
    $finalExecutablePath = "$rootPath/dist/HolocronToolset.app"
}

# Delete the final executable if it exists
if (Test-Path -Path $finalExecutablePath) {
    Remove-Item -Path $finalExecutablePath -Force
}

Write-Host "Extra PYTHONPATH paths:\n'$env:PYTHONPATH'\n\n"
$pyInstallerArgs = @{
    'exclude-module' = @(
        '',
        'dl_translate',
        'torch '
    )
    'clean' = $true
    'console' = $true
    'onefile' = $true
    'noconfirm' = $true
    'name' = "HolocronToolset"
    'distpath'=($rootPath + $pathSep + "dist")
#    'upx-dir' = "C:\GitHub\upx-win64"
    'icon'="resources/icons/sith.ico"
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
$argumentsArray += "toolset/__main__.py"

# Use the call operator with the arguments array
Write-Host "Executing command: $pythonExePath $argumentsArray"
& $pythonExePath $argumentsArray

# Check if the final executable exists
if (-not (Test-Path -Path $finalExecutablePath)) {
    Write-Error "Holocron Toolset could not be compiled, scroll up to find out why"   
} else {
    Write-Host "Holocron Toolset was compiled to '$finalExecutablePath'"
}
Set-Location -LiteralPath $current_working_dir

if (-not $this_noprompt) {
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
