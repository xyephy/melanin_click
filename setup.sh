#!/bin/bash

# Melanin Click Setup Script
# This script sets up the environment for Melanin Click

echo "Setting up Melanin Click environment..."

# Determine OS
OS=$(uname)
ARCH=$(uname -m)

echo "Detected: $OS on $ARCH"

# Handle OS-specific prerequisites
if [ "$OS" = "Darwin" ]; then
    echo "macOS detected, checking for tkinter dependencies..."
    
    # Check if homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo "Homebrew not found. Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    # Install python-tk with homebrew
    echo "Installing tkinter dependencies with Homebrew..."
    brew install python-tk
    
elif [ "$OS" = "Linux" ]; then
    echo "Linux detected, ensuring tkinter is available..."
    # Check for distribution
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
        
        case $DISTRO in
            ubuntu|debian|pop|mint|elementary)
                echo "Debian-based distribution detected: $DISTRO"
                sudo apt update
                sudo apt install -y python3-tk
                ;;
            fedora|rhel|centos|rocky)
                echo "Red Hat-based distribution detected: $DISTRO"
                sudo dnf install -y python3-tkinter
                ;;
            arch|manjaro|endeavouros)
                echo "Arch-based distribution detected: $DISTRO"
                sudo pacman -Sy tk
                ;;
            *)
                echo "Unknown Linux distribution. Please install tkinter manually."
                ;;
        esac
    else
        echo "Unable to detect Linux distribution. Please install tkinter manually."
    fi
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment. Please install Python 3.6+ first."
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
pip install tk

# Handle OS-specific requirements
if [ "$OS" = "Darwin" ]; then
    echo "macOS detected, setting TK_SILENCE_DEPRECATION=1"
    export TK_SILENCE_DEPRECATION=1
    echo "export TK_SILENCE_DEPRECATION=1" >> venv/bin/activate
elif [ "$OS" = "Linux" ]; then
    echo "Linux detected, checking for additional requirements..."
    # Check for terminal emulators
    if ! command -v xterm &> /dev/null && ! command -v gnome-terminal &> /dev/null && ! command -v konsole &> /dev/null; then
        echo "No terminal emulator found. Consider installing xterm:"
        echo "  Ubuntu/Debian: sudo apt-get install xterm"
        echo "  Fedora/RHEL: sudo dnf install xterm"
        echo "  Arch: sudo pacman -S xterm"
    fi
fi

# Set executable permissions
echo "Setting executable permissions..."
chmod +x melaninclick_macos.py

# Create launcher script
echo "Creating launcher script..."
cat > melaninclick.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
export TK_SILENCE_DEPRECATION=1
python melaninclick_macos.py
EOF

chmod +x melaninclick.sh

echo "Setup complete! Run ./melaninclick.sh to start the application." 