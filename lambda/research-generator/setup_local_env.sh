#!/bin/bash
# Script to set up the local environment with the correct dependency versions

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies from requirements.txt
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# Show installed versions
echo -e "\nInstalled package versions:"
pip list | grep -E "anthropic|boto3|requests"

echo -e "\nSetup complete! You can now run the test_locally.py script."
echo "Remember to activate the virtual environment with:"
echo "source venv/bin/activate" 