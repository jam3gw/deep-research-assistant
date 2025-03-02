"""
Utility functions for the research generator.
"""
import json

def extract_content(message):
    """
    Extract text content from an Anthropic API response
    """
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
            return " ".join(text_parts)
        elif isinstance(content, str):
            # If content is already a string
            return content
        else:
            # Fallback: convert to string representation
            return str(content)
    else:
        return str(message)

def build_response(status_code, body, include_cors=True):
    """Helper function to build responses, optionally with CORS headers."""
    response = {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
        },
        'body': json.dumps(body)
    }
    
    # Add CORS headers only if needed (not for Function URL invocations)
    if include_cors:
        response['headers'].update({
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST',
            'Access-Control-Allow-Headers': 'Content-Type'
        })
    
    return response 