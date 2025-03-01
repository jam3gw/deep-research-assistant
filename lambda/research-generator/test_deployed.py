#!/usr/bin/env python3
"""
Test script for the deployed research generator Lambda function.
This allows you to test the function via its API Gateway endpoint.

Usage:
    python test_deployed.py "climate change impacts on agriculture" https://your-api-endpoint.execute-api.region.amazonaws.com/prod/
    python test_deployed.py --depth 3 --sub-questions 4 --threshold 1 "climate change impacts on agriculture" https://your-api-endpoint.execute-api.region.amazonaws.com/prod/
"""

import sys
import json
import requests
import argparse

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test the deployed research generator Lambda function.')
    parser.add_argument('topic', type=str, help='The research topic to process')
    parser.add_argument('endpoint', type=str, help='The API Gateway endpoint URL')
    parser.add_argument('--threshold', '-t', type=int, choices=[0, 1, 2], default=None, 
                        help='Recursion threshold (0=normal, 1=conservative, 2=very conservative)')
    parser.add_argument('--depth', '-d', type=int, default=None, 
                        help='Maximum recursion depth (0-4)')
    parser.add_argument('--sub-questions', '-s', type=int, default=None, 
                        help='Maximum number of sub-questions (1-5)')
    args = parser.parse_args()
    
    # Get the topic and API endpoint from command line arguments
    topic = args.topic
    api_endpoint = args.endpoint.rstrip('/')
    
    # Ensure the endpoint ends with /research
    if not api_endpoint.endswith('/research'):
        api_endpoint += '/research'
    
    print(f"Testing research generation for topic: {topic}")
    print(f"Using API endpoint: {api_endpoint}")
    
    # Prepare the request payload
    payload = {
        'expression': topic
    }
    
    # Add optional parameters if provided
    if args.threshold is not None:
        payload['recursion_threshold'] = args.threshold
        print(f"Setting recursion threshold: {args.threshold}")
    
    if args.depth is not None:
        payload['max_recursion_depth'] = args.depth
        print(f"Setting max recursion depth: {args.depth}")
    
    if args.sub_questions is not None:
        payload['max_sub_questions'] = args.sub_questions
        print(f"Setting max sub questions: {args.sub_questions}")
    
    # Create a session with proxies disabled
    session = requests.Session()
    session.trust_env = False  # Disable automatic proxy detection
    
    # Make the API request
    try:
        print("Sending request to API...")
        response = session.post(api_endpoint, json=payload, timeout=60)
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Parse the response
        result = response.json()
        
        # Print the result
        print(f"\nAPI Response Status Code: {response.status_code}")
        
        if 'explanation' in result:
            print("\nGenerated Research:")
            print(result['explanation'])
        else:
            print("\nAPI Response:")
            print(json.dumps(result, indent=2))
        
        # Save to a file
        output_file = "deployed_research_output.json"
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nOutput saved to {output_file}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status code: {e.response.status_code}")
            try:
                error_data = e.response.json()
                print(f"Error response: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error response text: {e.response.text}")
        sys.exit(1)

if __name__ == "__main__":
    main() 