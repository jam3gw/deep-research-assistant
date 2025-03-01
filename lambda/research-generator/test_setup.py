#!/usr/bin/env python3
"""
Test script to verify that the virtual environment is set up correctly.
This script checks that all required libraries can be imported without errors.
"""

import sys
import json
import os
import boto3
import anthropic
import httpx

def main():
    print("Testing virtual environment setup...")
    
    # Print versions of key libraries
    print(f"Python version: {sys.version}")
    print(f"Anthropic version: {anthropic.__version__}")
    print(f"Boto3 version: {boto3.__version__}")
    print(f"Httpx version: {httpx.__version__}")
    
    # Test Anthropic client initialization
    try:
        # Initialize with a dummy key (no API call will be made)
        client = anthropic.Anthropic(api_key="sk-ant-dummy123")
        print("✅ Anthropic client initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing Anthropic client: {str(e)}")
        return 1
    
    print("\nAll libraries imported successfully!")
    print("The virtual environment is set up correctly.")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 