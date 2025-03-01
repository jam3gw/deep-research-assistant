#!/bin/bash
# Script to set up the local environment for testing the research generator

# Create and activate a virtual environment
echo "Creating virtual environment..."
python -m venv venv

# Activate the virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "Activating virtual environment on Windows..."
    source venv/Scripts/activate
else
    echo "Activating virtual environment on Unix-like system..."
    source venv/bin/activate
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Remind user to set API key
echo ""
echo "Setup complete! Before running the test script, set your Anthropic API key:"
echo "export ANTHROPIC_API_KEY=your_api_key"
echo ""
echo "Then run the test script with:"
echo "python test_locally.py \"What are the economic and environmental impacts of renewable energy adoption globally?\""
echo ""
echo "You can control the recursion behavior with the --threshold parameter:"
echo "python test_locally.py --threshold 0 \"Your question\"  # Normal recursion (more aggressive)"
echo "python test_locally.py --threshold 1 \"Your question\"  # Conservative recursion (default)"
echo "python test_locally.py --threshold 2 \"Your question\"  # Very conservative recursion (minimal)"
echo ""
echo "The results will be saved in the research_output directory." 