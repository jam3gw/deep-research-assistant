#!/usr/bin/env python3
"""
Test script for the deployed research generator Lambda function.
This allows you to test the function via its API Gateway endpoint.

Usage:
    python test_deployed.py "climate change impacts on agriculture" https://your-api-endpoint.execute-api.region.amazonaws.com/prod/
"""

import sys
import json
import requests

def main():
    if len(sys.argv) < 3:
        print("Usage: python test_deployed.py \"your research topic\" https://your-api-endpoint.execute-api.region.amazonaws.com/prod/")
        sys.exit(1)
    
    # Get the topic and API endpoint from command line arguments
    topic = sys.argv[1]
    api_endpoint = sys.argv[2].rstrip('/')
    
    # Ensure the endpoint ends with /research
    if not api_endpoint.endswith('/research'):
        api_endpoint += '/research'
    
    print(f"Testing research generation for topic: {topic}")
    print(f"Using API endpoint: {api_endpoint}")
    
    # Prepare the request payload
    payload = {
        'expression': topic
    }
    
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