#!/bin/bash

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
            brew update
            brew install powershell/tap/powershell
            brew install --cask powershell
        fi
    fi
    #if ! command -v pwsh > /dev/null; then
        #if command -v pacman > /dev/null; then
            #...
        #fi
    #fi
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
            
            echo If you are prompted to enter a password at this point, enter 'temppassword' without the ''
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

# Function to install PowerShell on macOS
install_powershell_mac() {

    which -s brew
    if [[ $? != 0 ]] ; then
        # Install Homebrew
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        echo 'eval $(/opt/homebrew/bin/brew shellenv)' >> ~/.zprofile
        eval $(/opt/homebrew/bin/brew shellenv)
        which -s brew
        if [[ $? != 0 ]] ; then
            echo "Could not install homebrew on your system. Attempting to install powershell via another method..."
            # Detect architecture
            ARCH=$(uname -m)
            PS_VERSION="7.2.17"  # The latest stable LTS mac version of Powershell
            PS_PKG_PREFIX="https://github.com/PowerShell/PowerShell/releases/download/v$PS_VERSION/powershell-$PS_VERSION"

            # Download the appropriate package based on architecture
            if [ "$ARCH" == "arm64" ]; then
                # Apple Silicon Mac
                curl -L -o "powershell-$PS_VERSION-osx-arm64.pkg" "$PS_PKG_PREFIX-osx-arm64.pkg"
            elif [ "$ARCH" == "x86_64" ]; then
                # Intel Mac
                curl -L -o "powershell-$PS_VERSION-osx-x64.pkg" "$PS_PKG_PREFIX-osx-x64.pkg"
            else
                echo "Unsupported architecture: $ARCH"
                exit 1
            fi
            sudo xattr -rd com.apple.quarantine ./powershell-$PS_VERSION-osx-$ARCH.pkg
            sudo installer -pkg ./powershell-$PS_VERSION-osx-$ARCH.pkg -target /
        else
            brew update
            brew install powershell/tap/powershell
            brew install --cask powershell
        fi
    else
        brew update
        brew install powershell/tap/powershell
        brew install --cask powershell
    fi
}

install_powershell_debian() {
    echo "Installing Powershell for debian..."
    sudo apt-get update
    sudo apt-get install -y wget
    source /etc/os-release
    wget -q https://packages.microsoft.com/config/debian/$VERSION_ID/packages-microsoft-prod.deb
    sudo dpkg -i packages-microsoft-prod.deb
    rm packages-microsoft-prod.deb
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
                        echo "CentOS version is less than 8.5, converting to alma linux..."
                    else
                        echo "CentOS version is 8.5 or higher, converting to alma linux..."
                    fi
                    sed -i -r 's|^(mirrorlist.+)$|#\1|g; s|^#baseurl=http://mirror.centos.org/\$contentdir/\$releasever/|baseurl=https://vault.centos.org/8.5.2111/|g' /etc/yum.repos.d/CentOS-*.repo
                    sudo yum update -y
                    curl -O https://raw.githubusercontent.com/AlmaLinux/almalinux-deploy/master/almalinux-deploy.sh
                    sudo bash almalinux-deploy.sh
                    sudo rpm --import https://repo.almalinux.org/almalinux/RPM-GPG-KEY-AlmaLinux && sudo bash almalinux-deploy.sh
                    cat /etc/redhat-release
                    sudo grubby --info DEFAULT | grep AlmaLinux
                    sudo yum update
                    sudo yum install -y powershell
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