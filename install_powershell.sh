#!/bin/bash

# Function to install PowerShell on Linux
determine_linux_powershell_installer() {
    # Determine if using apt-get (Debian-based) or yum/dnf (Red Hat-based)
    if command -v apt-get > /dev/null; then
        sudo apt-get update
        sudo apt-get install -y powershell
    elif command -v yum > /dev/null; then
        sudo yum install -y powershell
    elif command -v dnf > /dev/null; then
        sudo dnf install -y powershell
    elif command -v brew > /dev/null; then
        brew update
        brew install powershell/tap/powershell
        brew install --cask powershell
    else
        echo "Unsupported Linux distribution for automatic PowerShell installation."
        exit 1
    fi
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
    # install the requirements
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
                # Add checks for other distributions like fedora and centos
                *)
                    echo "Unsupported Linux distribution for automatic PowerShell installation. Attempting to install automatically with your package manager..."
                    determine_linux_powershell_installer
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