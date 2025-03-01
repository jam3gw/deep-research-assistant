import json
import os
import boto3
import logging
import requests
import re

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Anthropic API constants
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_API_VERSION = "2023-06-01"
MODEL = "claude-3-sonnet-20240229"

# Initialize AWS clients
secrets_manager = boto3.client('secretsmanager')

def get_anthropic_api_key():
    """
    Retrieves the Anthropic API key from AWS Secrets Manager
    """
    secret_name = os.environ.get('ANTHROPIC_API_KEY_SECRET_NAME')
    
    try:
        response = secrets_manager.get_secret_value(SecretId=secret_name)
        secret_string = response.get('SecretString')
        
        # Try to parse as JSON first
        try:
            secret_dict = json.loads(secret_string)
            # Check for common key names
            if 'apiKey' in secret_dict:
                return secret_dict['apiKey']
            elif 'key' in secret_dict:
                return secret_dict['key']
            elif 'value' in secret_dict:
                return secret_dict['value']
        except json.JSONDecodeError:
            # If not JSON, assume the secret is the raw API key
            return secret_string.strip()
            
        # If we got here, we couldn't find the key in the expected format
        logger.warning("API key not found in expected format, using raw secret string")
        return secret_string.strip()
    except Exception as e:
        logger.error(f"Error retrieving Anthropic API key: {str(e)}")
        raise

def call_anthropic_api(api_key, prompt, conversation_id):
    """
    Makes a request to the Anthropic API
    """
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": ANTHROPIC_API_VERSION
    }
    
    payload = {
        "model": MODEL,
        "max_tokens": 1024,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "metadata": {
            "conversation_id": conversation_id
        }
    }
    
    try:
        logger.info(f"Calling Anthropic API with prompt: {prompt[:50]}...")
        response = requests.post(ANTHROPIC_API_URL, headers=headers, json=payload)
        
        if response.status_code != 200:
            logger.error(f"Anthropic API error: {response.status_code} - {response.text}")
            
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Anthropic API: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response status: {e.response.status_code}")
            logger.error(f"Response body: {e.response.text}")
        raise

def text_to_ssml(text):
    """
    Converts text to SSML for better speech synthesis
    """
    # Basic SSML conversion - can be enhanced for better speech patterns
    cleaned_text = text
    cleaned_text = re.sub(r'&', '&amp;', cleaned_text)
    cleaned_text = re.sub(r'<', '&lt;', cleaned_text)
    cleaned_text = re.sub(r'>', '&gt;', cleaned_text)
    cleaned_text = re.sub(r'"', '&quot;', cleaned_text)
    cleaned_text = re.sub(r"'", '&apos;', cleaned_text)
    
    # Add pauses at punctuation
    ssml_text = cleaned_text
    ssml_text = re.sub(r'\.', '.<break time="500ms"/>', ssml_text)
    ssml_text = re.sub(r'\?', '?<break time="500ms"/>', ssml_text)
    ssml_text = re.sub(r'!', '!<break time="500ms"/>', ssml_text)
    ssml_text = re.sub(r',', ',<break time="300ms"/>', ssml_text)
    
    return f"<speak>{ssml_text}</speak>"

def lambda_handler(event, context):
    """
    Main Lambda handler function
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Extract information from the event
        prompt = event.get('prompt')
        conversation_id = event.get('conversationId', 'unknown')
        
        if not prompt:
            raise ValueError("No prompt provided in the event")
        
        # Get the Anthropic API key
        api_key = get_anthropic_api_key()
        
        # Call the Anthropic API
        response = call_anthropic_api(api_key, prompt, conversation_id)
        
        # Extract the assistant's response
        assistant_response = response['content'][0]['text']
        
        # Convert the response to SSML for better speech synthesis
        ssml_response = text_to_ssml(assistant_response)
        
        return {
            'statusCode': 200,
            'body': {
                'text': assistant_response,
                'ssml': ssml_response,
                'conversationId': conversation_id or response.get('id')
            }
        }
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        
        error_message = "I'm sorry, I encountered an error and couldn't process your request. Please try again later."
        
        return {
            'statusCode': 500,
            'body': {
                'error': str(e),
                'ssml': text_to_ssml(error_message)
            }
        } 