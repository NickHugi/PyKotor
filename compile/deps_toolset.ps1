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

if ((Get-OS) -eq "Mac") {
    & bash -c "brew install mpdecimal gstreamer pulseaudio fontconfig" 2>&1 | Write-Output 
} elseif (Test-Path -Path "/etc/os-release") {
    $command = ""
    $distro = (Get-Linux-Distro-Name)
    switch ($distro) {
        "debian" {  # untested
            $command = "sudo apt-get install libpulse-mainloop-glib0 libgstreamer-plugins-base1.0-dev gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly libgstreamer1.0-dev mesa-utils libgl1-mesa-glx libgl1-mesa-dri libgl1-mesa-glx libglu1-mesa libglu1-mesa-dev -y"
            break
        }
        "ubuntu" {  # export LIBGL_ALWAYS_SOFTWARE=1
            $command = "sudo apt-get install libpulse-mainloop-glib0 libgstreamer-plugins-base1.0-dev gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly libgstreamer1.0-dev mesa-utils libgl1-mesa-glx libgl1-mesa-dri libgl1-mesa-glx libglu1-mesa libglu1-mesa-dev -y"
            break
        }
        "fedora" {
            sudo dnf groupinstall "Development Tools" -y
            $command = "sudo dnf install binutils mesa-libGL-devel pulseaudio-libs-glib2 gstreamer1-plugins-base gstreamer1-plugins-good gstreamer1-plugins-bad-free gstreamer1-plugins-ugly-free gstreamer1-devel -y"
            break
        }
        "oracle" {
            sudo yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
            $command = "sudo dnf install binutils mesa-libGL-devel pulseaudio-libs-glib2 gstreamer1-plugins-base gstreamer1-plugins-good gstreamer1-plugins-bad-free gstreamer1-plugins-ugly-free gstreamer1-devel -y"
            break
        }
        "almalinux" {
            $command = "sudo dnf install binutils libglvnd-opengl pulseaudio-libs-glib2 pulseaudio-libs-devel gstreamer1-plugins-base gstreamer1-plugins-good gstreamer1-plugins-bad-free mesa-libGLw libX11 mesa-dri-drivers mesa-libGL mesa-libglapi -y"
            break
        }
        "alpine" {  # export LIBGL_ALWAYS_SOFTWARE=1
            $command = "sudo apk add binutils gstreamer gstreamer-dev gst-plugins-bad-dev gst-plugins-base-dev pulseaudio-qt pulseaudio pulseaudio-alsa mesa-gl mesa-glapi libx11 ttf-dejavu fontconfig"
            break
        }
        "arch" {
            Write-Host "Initializing pacman keyring..."
            sudo pacman-key --init
            sudo pacman-key --populate archlinux
            sudo pacman -Sy archlinux-keyring --noconfirm
            sudo pacman -Syu --noconfirm
            sudo pacman -S mesa libxcb xcb-util-wm xcb-util-keysyms xcb-util-image xcb-util-renderutil libxcomposite gtk3 atk mpdecimal pulseaudio pulseaudio-alsa gstreamer mesa libglvnd ttf-dejavu fontconfig gst-plugins-base gst-plugins-good gst-plugins-bad gst-plugins-ugly --noconfirm
            break
        }
    }

    if ($command -eq "") {
        Write-Warning "Dist '$distro' not supported for automated system package install, please install the dependencies if you experience problems."
    } else {
        Write-Host "Executing command: $command"
        $output = Invoke-Expression $command

        # Check if the output contains the error message
        if ($distro -eq "arch") {
            if ($output -match "error: failed to commit transaction (invalid or corrupted package)") {
                Write-Error "Detected error: No packages were upgraded. Please run the command `sudo pacman-key --refresh-keys` and try again."
                Write-Error $output
            }
        }
    }
}

Write-Host "Initializing python virtual environment..."
if ($this_noprompt) {
    . $rootPath/install_python_venv.ps1 -noprompt -venv_name $venv_name
} else {
    . $rootPath/install_python_venv.ps1 -venv_name $venv_name
}


Write-Host "Installing required packages to build the holocron toolset..."
. $pythonExePath -m pip install --upgrade pip --prefer-binary --progress-bar on
. $pythonExePath -m pip install pyinstaller --prefer-binary --progress-bar on
. $pythonExePath -m pip install -r ($rootPath + $pathSep + "Tools" + $pathSep + "HolocronToolset" + $pathSep + "requirements.txt") --prefer-binary --compile --progress-bar on
. $pythonExePath -m pip install -r ($rootPath + $pathSep + "Libraries" + $pathSep + "PyKotor" + $pathSep + "requirements.txt") --prefer-binary --compile --progress-bar on
. $pythonExePath -m pip install -r ($rootPath + $pathSep + "Libraries" + $pathSep + "PyKotorGL" + $pathSep + "requirements.txt") --prefer-binary --compile --progress-bar on
#. $pythonExePath -m pip install -r ($rootPath + $pathSep + "Libraries" + $pathSep + "PyKotorGL" + $pathSep + "optional.txt") --prefer-binary --compile --progress-bar on