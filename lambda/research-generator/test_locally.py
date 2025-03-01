#!/usr/bin/env python3
"""
Test script for the research generator Lambda function.
This allows you to test the function locally before deploying to AWS.

Usage:
    python test_locally.py "climate change impacts on agriculture"
"""

import sys
import json
import os
from lambda_function import generate_research_structure

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_locally.py \"your research topic\"")
        sys.exit(1)
    
    # Get the topic from command line arguments
    topic = sys.argv[1]
    print(f"Generating research structure for topic: {topic}")
    
    # Set environment variables (you'll need to set your API key)
    if 'ANTHROPIC_API_KEY' not in os.environ:
        print("Please set the ANTHROPIC_API_KEY environment variable")
        print("Example: export ANTHROPIC_API_KEY=your_api_key")
        sys.exit(1)
    
    # Create a mock secret in the environment
    os.environ['ANTHROPIC_API_KEY_SECRET_NAME'] = 'mock_secret'
    
    # Mock the get_anthropic_api_key function
    def mock_get_api_key():
        return os.environ['ANTHROPIC_API_KEY']
    
    # Replace the actual function with our mock
    import lambda_function
    lambda_function.get_anthropic_api_key = mock_get_api_key
    
    try:
        # Call the function
        result = generate_research_structure(topic)
        
        # Print the result
        print("\nGenerated Research Structure:")
        print(json.dumps(result, indent=2))
        
        # Save to a file
        output_file = "research_output.json"
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nOutput saved to {output_file}")
        
    except Exception as e:
        import traceback
        print(f"Error generating research structure: {str(e)}")
        print("Full traceback:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 