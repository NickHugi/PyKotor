param(
  [switch]$noprompt,
  [string]$venv_name = ".venv"
)
$this_noprompt = $noprompt

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$rootPath = (Resolve-Path -LiteralPath "$scriptPath/..").Path
Write-Host "The path to the script directory is: $scriptPath"
Write-Host "The path to the root directory is: $rootPath"

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

$qtApi = $env:QT_API
if (-not $qtApi) {
    $qtApi = "pyqt5"  # Default to PyQt5 if QT_API is not set
}

# Define the Qt version and modules to install based on $qtApi
$qtVersion = switch ($qtApi) {
    "pyqt5" { "5.15.2" } # Last LTS version of Qt5
    "pyside2" { "5.15.2" } # Last LTS version of Qt5
    "pyqt6" { "6.2.2" }  # A stable Qt6 version, adjust as needed
    "pyside6" { "6.2.2" }  # A stable Qt6 version, adjust as needed
    default { "5.15.2" }
}

if ($this_noprompt) {
    . $rootPath/install_python_venv.ps1 -noprompt -venv_name $venv_name
} else {
    . $rootPath/install_python_venv.ps1 -venv_name $venv_name
}

$useAqtInstall = $true
$qtInstallPath = "$rootPath/vendor/Qt"
$qtOs = $null
$qtArch = $null
if ((Get-OS) -eq "Mac") {
    $qtOs = "mac"
    $qtArch = "clang_64" # i'm not even going to bother to test wasm_32.
    switch ($qtApi) {
        "pyqt5"   { & bash -c "brew install qt5 -q" }
        "pyqt6"   { & bash -c "brew install qt6 -q" }
        "pyside2" { & bash -c "brew install qt5 -q" }  # PySide2 typically uses Qt5
        "pyside6" { & bash -c "brew install qt6 -q" }
        default   { & bash -c "brew install qt5 -q" }
    }
    . $pythonExePath -m pip install $qtApi qtpy -U --prefer-binary
} elseif ((Get-OS) -eq "Windows") {
    # Determine system architecture
    if ($env:PROCESSOR_ARCHITECTURE -eq "AMD64" -or $env:PROCESSOR_ARCHITEW6432 -eq "AMD64") {
        Write-Output "System architecture determined as: 64-bit (AMD64)"
    } else {
        Write-Output "System architecture determined as: 32-bit"
    }

    # Determine Python architecture
    try {
        $pythonArchOutput = & $pythonExePath -c "import platform; print(platform.architecture()[0])" | Out-String
    } catch {
        Write-Error "Failed to determine Python architecture"
        $_.Exception | Out-String | Write-Output
        exit 1
    }
    
    Write-Output "Python architecture command output: $pythonArchOutput"
    
    if ($pythonArchOutput -match "64bit") {
        $qtArch = "win64_msvc2015_64"
        Write-Output "Python architecture determined as: 64-bit"
    } else {
        $qtArch = "win32_msvc2015"
        Write-Output "Python architecture determined as: 32-bit"
    }

    # Set the Qt installation directory based on common environment variables or default to a local 'Qt' directory
    if ($null -ne $env:GITHUB_WORKSPACE -and (Test-Path $env:GITHUB_WORKSPACE)) {
        $qtInstallPath = Join-Path $env:GITHUB_WORKSPACE "Qt"
        Write-Output "Aqt installation path set to GITHUB_WORKSPACE: $qtInstallPath"
    } elseif (Test-Path $env:USERPROFILE) {
        $qtInstallPath = Join-Path $env:USERPROFILE "Qt"
        Write-Output "Aqt installation path set to USERPROFILE: $qtInstallPath"
    } else {
        $qtInstallPath = Join-Path $PWD "Qt"
        Write-Output "Aqt installation path set to current directory: $qtInstallPath"
    }
    $qtOs = "windows"
} elseif (Test-Path -Path "/etc/os-release") {
    $qtArch = "gcc_64"
    $qtOs = "linux"
    $distro = (Get-Linux-Distro-Name)
    switch ($distro) {
        "debian" {  # untested
            sudo apt-get update
            sudo apt-get install libicu-dev libunwind-dev libwebp-dev liblzma-dev libjpeg-dev libtiff-dev libquadmath0 libgfortran5 libopenblas-dev libxau-dev libxcb1-dev python3-opengl python3-pyqt5 libpulse-mainloop-glib0 libgstreamer-plugins-base1.0-dev gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly libgstreamer1.0-dev mesa-utils libgl1-mesa-glx libgl1-mesa-dri qtbase5-dev qtchooser qt5-qmake qtbase5-dev-tools libgl1-mesa-glx libglu1-mesa libglu1-mesa-dev libqt5gui5 libqt5core5a libqt5dbus5 libqt5widgets5 -y
            break
        }
        "ubuntu" {  # export LIBGL_ALWAYS_SOFTWARE=1
            sudo apt-get update
            sudo apt-get install libicu-dev libunwind-dev libwebp-dev liblzma-dev libjpeg-dev libtiff-dev libquadmath0 libgfortran5 libopenblas-dev libxau-dev libxcb1-dev python3-opengl python3-pyqt5 libpulse-mainloop-glib0 libgstreamer-plugins-base1.0-dev gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly libgstreamer1.0-dev mesa-utils libgl1-mesa-glx libgl1-mesa-dri qtbase5-dev qtchooser qt5-qmake qtbase5-dev-tools libgl1-mesa-glx libglu1-mesa libglu1-mesa-dev libqt5gui5 libqt5core5a libqt5dbus5 libqt5widgets5 -y
            break
        }
        "fedora" {
            sudo dnf groupinstall "Development Tools" -y
            sudo dnf install binutils mesa-libGL-devel python3-pyopengl PyQt5 pulseaudio-libs-glib2 gstreamer1-plugins-base gstreamer1-plugins-good gstreamer1-plugins-bad-free gstreamer1-plugins-ugly-free gstreamer1-devel -y
            break
        }
        "oracle" {
            sudo yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
            sudo dnf install binutils PyQt5 mesa-libGL-devel pulseaudio-libs-glib2 gstreamer1-plugins-base gstreamer1-plugins-good gstreamer1-plugins-bad-free gstreamer1-plugins-ugly-free gstreamer1-devel -y
            break
        }
        "almalinux" {
            sudo dnf install binutils libglvnd-opengl python3-qt5 python3-pyqt5-sip pulseaudio-libs-glib2 pulseaudio-libs-devel gstreamer1-plugins-base gstreamer1-plugins-good gstreamer1-plugins-bad-free mesa-libGLw libX11 mesa-dri-drivers mesa-libGL mesa-libglapi -y
            break
        }
        "alpine" {  # export LIBGL_ALWAYS_SOFTWARE=1
            sudo apk add binutils gstreamer gstreamer-dev gst-plugins-bad-dev gst-plugins-base-dev pulseaudio-qt pulseaudio pulseaudio-alsa py3-opengl qt5-qtbase-x11 qt5-qtbase-dev mesa-gl mesa-glapi qt5-qtbase-x11 libx11 ttf-dejavu fontconfig
            break
        }
        "arch" {
            Write-Host "Initializing pacman keyring..."
            sudo pacman-key --init
            sudo pacman-key --populate archlinux
            sudo pacman -Sy archlinux-keyring --noconfirm
            sudo pacman -Syu --needed mesa libxcb qt5-base qt5-wayland xcb-util-wm xcb-util-keysyms xcb-util-image xcb-util-renderutil python-opengl libxcomposite gtk3 atk mpdecimal python-pyqt5 qt5-base qt5-multimedia qt5-svg pulseaudio pulseaudio-alsa gstreamer mesa libglvnd ttf-dejavu fontconfig gst-plugins-base gst-plugins-good gst-plugins-bad gst-plugins-ugly --noconfirm
            break
        }
    }
}


if ($useAqtInstall -eq $true) {  # Windows seems to always have qt5/6?
    # Combine the new path with the current PATH
    $origUserPath = [System.Environment]::GetEnvironmentVariable("PATH", [System.EnvironmentVariableTarget]::User)
    if (-not $origUserPath -contains $qtInstallPath) {
        $combinedPath = $origUserPath + ";" + $qtInstallPath
        [System.Environment]::SetEnvironmentVariable("PATH", $combinedPath, [System.EnvironmentVariableTarget]::User)  # [System.EnvironmentVariableTarget]::Machine for system PATH
        Write-Host "Added '$qtInstallPath' to user's PATH env"
    }
    $origCurPath = $env:PATH
    if (-not $origCurPath -contains $qtInstallPath) {
        $env:PATH = $env:PATH + ";" + $qtInstallPath
        Write-Host "Added '$qtInstallPath' to cur PATH env"
    }

    # Execute the aqtinstall command directly with arguments
    Write-Output "Executing $pythonExePath -m aqt install-qt $qtOs desktop $qtVersion $qtArch -m qtwebglplugin qtquick3d qtdatavis3d qt5compat --outputdir=$qtInstallPath"
    . $pythonExePath -m aqt install-qt $qtOs desktop $qtVersion $qtArch -m qtwebglplugin qtquick3d qtdatavis3d --outputdir=$qtInstallPath 2>&1 | Out-String | Write-Output
    if ($LastExitCode -ne 0) {
        Write-Output "Qt installation failed with exit code $LastExitCode"
    }
}


Write-Host "Installing pip packages to run the holocron toolset..."
. $pythonExePath -m pip install --upgrade pip --prefer-binary --progress-bar on
switch ($qtApi) {
    "pyqt5" {
        . $pythonExePath -m pip install -U PyQt5 PyQt5-Qt5 PyQt5-sip --prefer-binary --progress-bar on
    }
    "pyqt6" {
        . $pythonExePath -m pip install -U PyQt6 --prefer-binary --progress-bar on
    }
    "pyside2" {
        . $pythonExePath -m pip install -U PySide2 --prefer-binary --progress-bar on
    }
    "pyside6" {
        . $pythonExePath -m pip install -U PySide6 --prefer-binary --progress-bar on
    }
    default {
        . $pythonExePath -m pip install -U PyQt5 PyQt5-Qt5 PyQt5-sip --prefer-binary --progress-bar on
    }
}
. $pythonExePath -m pip install pyinstaller --prefer-binary --progress-bar on
. $pythonExePath -m pip install -r ($rootPath + $pathSep + "Tools" + $pathSep + "HolocronToolset" + $pathSep + "requirements.txt") --prefer-binary --compile --progress-bar on
. $pythonExePath -m pip install -r ($rootPath + $pathSep + "Libraries" + $pathSep + "PyKotor" + $pathSep + "requirements.txt") --prefer-binary --compile --progress-bar on
. $pythonExePath -m pip install -r ($rootPath + $pathSep + "Libraries" + $pathSep + "PyKotorGL" + $pathSep + "requirements.txt") --prefer-binary --compile --progress-bar on
#. $pythonExePath -m pip install -r ($rootPath + $pathSep + "Libraries" + $pathSep + "PyKotorGL" + $pathSep + "optional.txt") --prefer-binary --compile --progress-bar on