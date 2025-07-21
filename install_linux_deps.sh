#!/bin/bash

# Melanin Click Linux Dependencies Installer
# This script installs the necessary dependencies for Melanin Click on Linux

echo "Installing dependencies for Melanin Click on Linux..."

# Detect distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
else
    echo "Unable to detect Linux distribution."
    exit 1
fi

# Install dependencies based on distribution
case $DISTRO in
    ubuntu|debian|pop|mint|elementary)
        echo "Detected Debian-based distribution: $DISTRO"
        sudo apt update
        sudo apt install -y python3 python3-pip python3-venv python3-tk xterm wget git
        ;;
    fedora|rhel|centos|rocky)
        echo "Detected Red Hat-based distribution: $DISTRO"
        sudo dnf install -y python3 python3-pip python3-tkinter xterm wget git
        ;;
    arch|manjaro|endeavouros)
        echo "Detected Arch-based distribution: $DISTRO"
        sudo pacman -Sy python python-pip tk xterm wget git
        ;;
    opensuse|suse)
        echo "Detected openSUSE distribution: $DISTRO"
        sudo zypper install -y python3 python3-pip python3-tk xterm wget git
        ;;
    *)
        echo "Unsupported distribution: $DISTRO"
        echo "Please install the following packages manually:"
        echo "- Python 3"
        echo "- Python 3 pip"
        echo "- Python 3 Tkinter"
        echo "- xterm (or another terminal emulator)"
        echo "- wget"
        echo "- git"
        exit 1
        ;;
esac

echo "Dependencies installed successfully!"
echo "Now run ./setup.sh to set up the Melanin Click environment." 