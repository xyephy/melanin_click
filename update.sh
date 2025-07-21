#!/bin/bash

# Melanin Click Update Script
# This script checks for and applies updates to Melanin Click

echo "Checking for Melanin Click updates..."

# Determine OS
OS=$(uname)
ARCH=$(uname -m)

echo "System: $OS on $ARCH"

# Activate the virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Virtual environment activated."
else
    echo "Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Check if git is available
if ! command -v git &> /dev/null; then
    echo "Git is not installed. Please install git to enable updates."
    exit 1
fi

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "This doesn't appear to be a git repository. Cannot update."
    exit 1
fi

# Fetch latest changes
echo "Fetching latest changes..."
git fetch

# Check if we're behind the remote repository
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u})
BASE=$(git merge-base @ @{u})

if [ $LOCAL = $REMOTE ]; then
    echo "Melanin Click is already up to date."
elif [ $LOCAL = $BASE ]; then
    echo "Updates available. Applying updates..."
    
    # Backup the configuration
    if [ -f "config.json" ]; then
        cp config.json config.json.bak
        echo "Configuration backed up."
    fi
    
    # Pull the latest changes
    git pull
    
    # Restore the configuration
    if [ -f "config.json.bak" ]; then
        cp config.json.bak config.json
        echo "Configuration restored."
    fi
    
    # Update dependencies
    pip install -r requirements.txt
    
    echo "Update completed successfully!"
    echo "Please restart Melanin Click to apply the changes."
elif [ $REMOTE = $BASE ]; then
    echo "Local changes detected. Cannot update automatically."
    echo "Please commit or stash your changes and try again."
else
    echo "Branches have diverged. Cannot update automatically."
    echo "Please contact support for assistance."
fi

# Deactivate virtual environment
deactivate 