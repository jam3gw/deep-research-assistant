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
echo "You can control the behavior with the following parameters:"
echo ""
echo "Recursion threshold (controls how conservative the system is about breaking down questions):"
echo "python test_locally.py --threshold 0 \"Your question\"  # Normal recursion (more aggressive)"
echo "python test_locally.py --threshold 1 \"Your question\"  # Conservative recursion (default)"
echo "python test_locally.py --threshold 2 \"Your question\"  # Very conservative recursion (minimal)"
echo ""
echo "Maximum recursion depth (how deep the question tree can go, max 4):"
echo "python test_locally.py --depth 2 \"Your question\"  # Default depth"
echo "python test_locally.py --depth 4 \"Your question\"  # Maximum allowed depth"
echo ""
echo "Maximum sub-questions (how many sub-questions per node, max 5):"
echo "python test_locally.py --sub-questions 3 \"Your question\"  # Default"
echo "python test_locally.py --sub-questions 5 \"Your question\"  # Maximum allowed"
echo ""
echo "You can combine these parameters:"
echo "python test_locally.py --depth 3 --sub-questions 4 --threshold 1 \"Your complex question\""
echo ""
echo "The results will be saved in the research_output directory." 