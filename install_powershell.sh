#!/bin/bash

if command -v pwsh > /dev/null 2>&1; then
    echo "PowerShell already installed, nothing to do."
    pwsh --version
    exit 0
else
    echo "PowerShell is not installed."
    # Proceed with installation steps...
fi

# Default values
noprompt=false

# Parse command-line arguments
while getopts ":n" opt; do
    case ${opt} in
        n )
            noprompt=true
            ;;
        \? )
            echo "Usage: $0 [-n]"
            echo "[-n] - Don't prompt for any instruction (default is to prompt)"
            exit 1
            ;;
    esac
done
#shift $((OPTIND -1)) uncomment if a second cmdline arg is needed

# Function to install PowerShell on Linux
fallback_install_pwsh() {
    if ! command -v pwsh > /dev/null; then
        if command -v apt-get > /dev/null; then
            echo "Found 'apt-get' command"
            install_powershell_ubuntu
        fi
    fi
    if ! command -v pwsh > /dev/null; then
        if command -v dnf > /dev/null; then
            source /etc/os-release
            echo "Found 'dnf' command"
            sudo dnf update -y
            echo Updated, installing powershell...
            if [[ $ID == "almalinux" ]]; then
                sudo dnf install -y https://packages.microsoft.com/config/alma/$VERSION_ID/packages-microsoft-prod.rpm
            elif [[ $ID_LIKE == "fedora" ]]; then
                sudo dnf install -y https://packages.microsoft.com/config/fedora/$VERSION_ID/packages-microsoft-prod.rpm
            elif [[ $ID_LIKE == *"fedora"* ]]; then
                sudo dnf install -y https://packages.microsoft.com/config/fedora/$VERSION_ID/packages-microsoft-prod.rpm
            elif [[ $ID_LIKE == *"rhel"* ]]; then
                sudo dnf install -y https://packages.microsoft.com/config/rhel/$VERSION_ID/packages-microsoft-prod.rpm
            elif [[ $ID_LIKE == *"centos"* ]]; then
                sudo dnf install -y https://packages.microsoft.com/config/centos/$VERSION_ID/packages-microsoft-prod.rpm
            fi
            sudo dnf install -y powershell
        fi
    fi
    if ! command -v pwsh > /dev/null; then
        if command -v snap > /dev/null; then
            echo "Installing PowerShell via Snap..."
            sudo snap install powershell --classic
        fi
    fi
    if ! command -v pwsh > /dev/null; then
        if command -v yum > /dev/null; then
            echo "Found 'yum' command"
            sudo yum update
            sudo yum install -y powershell
        fi
    fi
    if ! command -v pwsh > /dev/null; then
        if command -v zypper > /dev/null; then
            echo "Found 'zypper' command"
            sudo zypper install -y https://packages.microsoft.com/config/sles/15/packages-microsoft-prod.rpm
            sudo zypper refresh
            sudo zypper install -y powershell
        fi
    fi
    if ! command -v pwsh > /dev/null; then
        if command -v brew > /dev/null; then
            echo "Found 'brew' command"
            install_powershell_brew
        fi
    fi
    if ! command -v pwsh > /dev/null; then
        if command -v pacman > /dev/null; then
            install_powershell_archlinux
        fi
    fi
    if ! command -v pwsh > /dev/null; then
        if command -v flatpak > /dev/null; then
            echo "Installing PowerShell via Flatpak..."
            flatpak install flathub com.microsoft.powershell -y
        fi
    fi

    if command -v pwsh > /dev/null; then
        echo "PowerShell installation was successful."
    else
        echo "PowerShell installation failed."
        exit 1
    fi
}

install_powershell_archlinux() {
    sudo pacman-key --init
    sudo pacman-key --populate archlinux
    sudo pacman -Syu archlinux-keyring --noconfirm
    sudo pacman -Syy --noconfirm
    # Find the exact name of the package (if available in official repos)
    # It's more efficient to install from official repos if available
    sudo pacman -S --needed --noconfirm powershell-bin || {

        # If the package isn't found in the official repositories, proceed with AUR
        sudo pacman -S --needed --noconfirm git base-devel

        # Clone the AUR repository for powershell-bin
        git clone https://aur.archlinux.org/powershell-bin.git
        cd powershell-bin

        # Inspect the PKGBUILD - always good practice
        cat PKGBUILD

        if [ "$(id -u)" -eq 0 ]; then
            echo "This script should not be run as root, using a temporary user named 'tempuser'..."
            TEMP_USER="tempuser"  # makepkg cannot be run as root
            TEMP_PASSWORD="temppassword"
            TEMP_ENTRY='tempuser ALL=(ALL:ALL) NOPASSWD:ALL'
            # Check if tempuser exists, create if not
            if ! id "$TEMP_USER" &>/dev/null; then
                if command -v adduser > /dev/null; then
                    sudo adduser --disabled-password --gecos "" $TEMP_USER
                else
                    sudo useradd -M --no-create-home $TEMP_USER
                    #useradd -m -c "" "$new_username"
                    #echo "$TEMP_USER:$TEMP_PASSWORD" | sudo chpasswd
                fi
            fi
            # Check if the entry already exists, and if not, append it to the sudoers file
            if ! grep -P "^${TEMP_ENTRY}" /etc/sudoers; then
                echo "$TEMP_ENTRY" | sudo EDITOR='tee -a' visudo >/dev/null
                echo "Entry added successfully."
            else
                echo "Entry already exists."
            fi

            # Change ownership to tempuser for the build directory
            sudo chown -R "$TEMP_USER:$TEMP_USER" "../powershell-bin"

            echo If you are prompted to enter a password at this point, enter temppassword
            # Attempt to build the package as tempuser
            if ! echo "$TEMP_PASSWORD" | sudo -S -u "$TEMP_USER" makepkg -si --noconfirm; then
                # If makepkg fails, reset the ownership to root before exiting
                sudo chown -R root:root "../powershell-bin"
                exit 1
            fi
            # Remove the specific sudoers entry
            sudo sed -i "/^${TEMP_ENTRY}$/d" /etc/sudoers

            # Validate that the sudoers file is still OK (important!)
            sudo visudo -c

            if [ $? -eq 0 ]; then
                echo "Entry removed successfully and sudoers file is valid."
            else
                echo "An error occurred. The sudoers file may be invalid. Restoring from backup."
                sudo cp /etc/sudoers.bak /etc/sudoers
            fi

            # Reset ownership after successful build
            sudo chown -R root:root "../powershell-bin"

            # Remove the temporary user
            if command -v userdel > /dev/null; then
                sudo userdel -r "$TEMP_USER" 2>/dev/null || true
            elif command -v deluser > /dev/null; then
                sudo deluser --remove-home "$TEMP_USER" 2>/dev/null || true
            else
                echo "User deletion command not found!"
            fi
        else
            # Build and install the package without running as root and without confirmation
            makepkg -si --noconfirm
        fi
    }
}

# Install powershell without Homebrew
install_powershell_mac_fallback() {
    echo "Downloading and installing the powershell direct pkg"
    # Detect architecture
    ARCH=$(uname -m)
    PS_VERSION="7.2.18"  # The latest stable LTS mac version of Powershell
    PS_PKG_PREFIX="https://github.com/PowerShell/PowerShell/releases/download/v$PS_VERSION/"

    # Apple Silicon Mac
    if [ "$ARCH" == "arm64" ]; then
        PKG_FILENAME="powershell-$PS_VERSION-osx-arm64.pkg"
    # Intel Mac
    elif [ "$ARCH" == "x86_64" ]; then
        PKG_FILENAME="powershell-$PS_VERSION-osx-x64.pkg"
    # Unknown architecture
    else
        echo "Unsupported architecture: $ARCH"
        exit 1
    fi

    echo "Downloading $PKG_FILENAME from $PS_PKG_PREFIX... please wait..."
    curl -L -o "$PKG_FILENAME" "$PS_PKG_PREFIX/$PKG_FILENAME"

    full_version=$(sw_vers -productVersion)  # Get the macOS full version number
    major_version=$(echo "$full_version" | cut -d '.' -f 1)  # Extract the major version number (before the first dot)
    echo "Version of mac is $full_version major version $major_version on arch $ARCH"
    if [[ $major_version -ge 11 ]]; then
        echo "This MacOS is running Big Sur or later, so downloaded pwsh package is most likely quarantined, let's call xattr now"
        sudo xattr -rd com.apple.quarantine $PKG_FILENAME
    fi

    echo "Installing $PKG_FILENAME"
    sudo installer -pkg $PKG_FILENAME -target /
}

install_powershell_brew() {
    brew update
    if [ $? -ne 0 ]; then
        echo "Error: 'brew update' failed."
        install_powershell_mac_fallback
    fi
    brew install powershell/tap/powershell
    if [ $? -ne 0 ]; then
        echo "Error: 'brew install powershell/tap/powershell' failed."
        install_powershell_mac_fallback
    fi
    brew install --cask powershell
    if [ $? -ne 0 ]; then
        echo "Error: 'brew install --cask powershell' failed."
        install_powershell_mac_fallback
    fi
}

# Function to install PowerShell on macOS
install_powershell_mac() {

    if ! command -v brew &>/dev/null; then

        # Install Homebrew
        echo "Installing Powershell through Homebrew is recommended (by microsoft themselves)"
        echo "Install HomeBrew now? (y) otherwise attempt to fallback to direct pkg download (n)"
        if [ $noprompt == false ]; then
            read -p "Enter your choice (y/N): " user_choice
        else
            user_choice = "y"
        fi

        if [ $user_choice == "y" ] || [ $user_choice == "Y"]; then
            echo "Installing HomeBrew... please wait..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            echo 'eval $(/opt/homebrew/bin/brew shellenv)' >> ~/.zprofile
            eval $(/opt/homebrew/bin/brew shellenv)

            if ! command -v brew &>/dev/null; then
                echo "Could not install homebrew on your system. Attempting to install powershell via another method..."
                install_powershell_mac_fallback
            else
                install_powershell_brew
            fi
        else
            echo "Skipping install of HomeBrew and installing powershell directly from the pkg..."
            install_powershell_mac_fallback
        fi
    else
        install_powershell_brew
    fi
}

install_powershell_debian() {
    echo "Installing Powershell for debian..."
    sudo apt-get update
    sudo apt-get install -y wget
    source /etc/os-release
    if ! command -v wget &>/dev/null; then
        if ! command -v curl &>/dev/null; then
            echo "Error: Neither wget nor curl is available. Cannot download the file."
            exit 1
        else
            curl -L -o packages-microsoft-prod.deb https://packages.microsoft.com/config/debian/$VERSION_ID/packages-microsoft-prod.deb
        fi
    else
        wget -q https://packages.microsoft.com/config/debian/$VERSION_ID/packages-microsoft-prod.deb
    fi
    sudo dpkg -i packages-microsoft-prod.deb
    rm -f packages-microsoft-prod.deb
    sudo apt-get update
    sudo apt-get install -y powershell
}

install_powershell_ubuntu() {
    echo "Installing Powershell for ubuntu..."
    sudo apt-get update
    sudo apt-get install -y wget apt-transport-https software-properties-common
    source /etc/os-release
    wget -q https://packages.microsoft.com/config/ubuntu/$VERSION_ID/packages-microsoft-prod.deb
    sudo dpkg -i packages-microsoft-prod.deb
    rm packages-microsoft-prod.deb
    sudo apt-get update
    sudo apt-get install -y powershell
}

install_powershell_rhel() {
    echo "Installing Powershell for rhel systems..."
    sudo dnf install bc -y
    source /etc/os-release
    if [ $(bc<<<"$VERSION_ID < 8") = 1 ]
    then majorver=7
    elif [ $(bc<<<"$VERSION_ID < 9") = 1 ]
    then majorver=8
    else majorver=9
    fi
    curl -sSL -O https://packages.microsoft.com/config/rhel/$majorver/packages-microsoft-prod.rpm
    sudo rpm -i packages-microsoft-prod.rpm
    rm packages-microsoft-prod.rpm
    # RHEL 7.x uses yum and RHEL 8+ uses dnf
    if [ $(bc<<<"$majorver < 8") ]
    then
        sudo yum update
        sudo yum install powershell -y
    else
        sudo dnf update
        sudo dnf install powershell -y
    fi
}

install_powershell_alpine() {
    echo "Installing Powershell for alpine..."
    # install the requirements
    apk add sudo
    sudo apk add --no-cache \
        ca-certificates \
        less \
        ncurses-terminfo-base \
        krb5-libs \
        libgcc \
        libintl \
        libssl1.1 \
        libstdc++ \
        tzdata \
        userspace-rcu \
        zlib \
        icu-libs \
        curl

    sudo apk -X https://dl-cdn.alpinelinux.org/alpine/edge/main add --no-cache \
        lttng-ust

    curl -L https://github.com/PowerShell/PowerShell/releases/download/v7.2.18/powershell-7.2.18-linux-alpine-x64.tar.gz -o /tmp/powershell.tar.gz
    sudo mkdir -p /opt/microsoft/powershell/7
    sudo tar zxf /tmp/powershell.tar.gz -C /opt/microsoft/powershell/7
    sudo chmod +x /opt/microsoft/powershell/7/pwsh
    sudo ln -s /opt/microsoft/powershell/7/pwsh /usr/bin/pwsh
}

# Determine OS and call the appropriate installation function
OS=$(uname -s)
case "$OS" in
    Darwin)
        install_powershell_mac
        ;;
    Linux)
        # Source the os-release to get the distribution ID and VERSION_ID
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            case "$ID" in
                debian)
                    install_powershell_debian
                    ;;
                ubuntu)
                    install_powershell_ubuntu
                    ;;
                alpine)
                    install_powershell_alpine
                    ;;
                fedora)
                    echo "Installing powershell for fedora"
                    sudo rpm --import https://packages.microsoft.com/keys/microsoft.asc
                    curl https://packages.microsoft.com/config/rhel/7/prod.repo | sudo tee /etc/yum.repos.d/microsoft.repo
                    sudo dnf update -y
                    echo Updated, installing powershell...
                    sudo dnf install -y https://packages.microsoft.com/config/fedora/$VERSION_ID/packages-microsoft-prod.rpm
                    sudo dnf install -y powershell
                    ;;
                centos)
                    echo "Installing Powershell for centos..."
                    # Obtain CentOS version
                    centos_version=$(rpm -E %{rhel})

                    # Compare version to see if it's less than 8.5
                    if [[ "$centos_version" -lt 85 ]]; then
                        echo "CentOS version is less than 8.5, considering converting to AlmaLinux..."
                    else
                        echo "CentOS version is 8.5 or higher, considering converting to AlmaLinux..."
                    fi
                    echo "You are currently running CentOS version $centos_version. The package manager 'yum' on here reached EOL and is no longer hosted."
                    echo "In order to install powershell, we must convert you to alma linux through their supported process (recommended)."
                    echo "WARNING: Converting CentOS to AlmaLinux is a significant change and not reversible. This process will change your CentOS distribution to AlmaLinux to continue with the PowerShell installation."
                    echo "Do you want to continue with the conversion?"
                    if [ $noprompt == false ]; then
                        read -p "Enter your choice (y/N): " user_choice
                    else
                        user_choice = "y"
                    fi

                    if [[ $user_choice == "y" ]]; then
                        sed -i -r 's|^(mirrorlist.+)$|#\1|g; s|^#baseurl=http://mirror.centos.org/\$contentdir/\$releasever/|baseurl=https://vault.centos.org/8.5.2111/|g' /etc/yum.repos.d/CentOS-*.repo
                        sudo yum update -y
                        echo "Downloading AlmaLinux conversion script..."
                        curl -O https://raw.githubusercontent.com/AlmaLinux/almalinux-deploy/master/almalinux-deploy.sh
                        echo "Converting to AlmaLinux. This may take some time..."
                        sudo bash almalinux-deploy.sh
                        sudo rpm --import https://repo.almalinux.org/almalinux/RPM-GPG-KEY-AlmaLinux && sudo bash almalinux-deploy.sh
                        echo "Conversion to AlmaLinux completed."
                        cat /etc/redhat-release
                        sudo grubby --info DEFAULT | grep AlmaLinux
                        sudo yum update
                        sudo yum install -y powershell
                        echo "PowerShell has been installed successfully."
                    else
                        echo "Conversion canceled by the user. Attempting fallbacks..."
                        fallback_install_pwsh
                    fi
                    ;;
                almalinux)
                    echo "Installing Powershell for almalinux..."
                    sudo dnf install -y https://github.com/PowerShell/PowerShell/releases/download/v7.1.4/powershell-7.1.4-1.centos.8.x86_64.rpm
                    ;;
                *)
                    if [ -f /etc/redhat-release ]; then
                        install_powershell_rhel
                    else
                        echo "Unsupported Linux distribution for automatic PowerShell installation. Attempting to install automatically with your package manager..."
                        fallback_install_pwsh
                    fi
                    ;;
            esac
        else
            echo "Cannot determine Linux distribution."
            exit 1
        fi
        ;;
    *)
        echo "Unsupported operating system."
        exit 1
        ;;
esac
