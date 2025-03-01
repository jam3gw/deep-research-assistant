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
from anthropic import Anthropic

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_locally.py \"your research topic\"")
        sys.exit(1)
    
    # Get the topic from command line arguments
    topic = sys.argv[1]
    print(f"Generating research for topic: {topic}")
    
    # Set environment variables (you'll need to set your API key)
    if 'ANTHROPIC_API_KEY' not in os.environ:
        print("Please set the ANTHROPIC_API_KEY environment variable")
        print("Example: export ANTHROPIC_API_KEY=your_api_key")
        sys.exit(1)
    
    api_key = os.environ['ANTHROPIC_API_KEY']
    
    try:
        # Initialize Anthropic client
        print("Initializing Anthropic client...")
        client = Anthropic(api_key=api_key)
        
        # Create the message for Claude
        prompt = f"""You are a research assistant.
        
        A student has asked you to research this prompt: {topic}
        """
        
        # Get response from Claude using the Messages API
        print("Sending request to Anthropic API...")
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            temperature=0.5,
            system="You are a helpful and friendly research assistant that explains complex concepts in simple terms. Format your response with HTML tags for better readability: use <h3> for section titles, <p> for paragraphs, <ol> and <li> for numbered steps, <strong> for emphasis, and <hr> for section dividers.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract the response text
        print("Response received from Anthropic API.")
        
        # Extract text based on the response structure
        explanation = ""
        if hasattr(message, 'content'):
            content = message.content
            if isinstance(content, list):
                # If content is a list of blocks
                text_parts = []
                for item in content:
                    if hasattr(item, 'text'):
                        text_parts.append(item.text)
                    elif hasattr(item, 'value'):
                        text_parts.append(item.value)
                    elif isinstance(item, str):
                        text_parts.append(item)
                explanation = " ".join(text_parts)
            elif isinstance(content, str):
                # If content is already a string
                explanation = content
            else:
                # Fallback: convert to string representation
                explanation = str(content)
        else:
            explanation = str(message)
        
        # Print the result
        print("\nGenerated Research:")
        print(explanation)
        
        # Save to a file
        output_file = "research_output.json"
        with open(output_file, "w") as f:
            json.dump({"explanation": explanation}, f, indent=2)
        print(f"\nOutput saved to {output_file}")
        
    except Exception as e:
        import traceback
        print(f"Error generating research: {str(e)}")
        print("Full traceback:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 