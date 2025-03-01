import json
import os
import boto3
import logging
import anthropic
from typing import Dict, List, Any, Optional

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
secretsmanager = boto3.client('secretsmanager')

def get_anthropic_api_key() -> str:
    """Retrieve the Anthropic API key from AWS Secrets Manager."""
    try:
        secret_name = os.environ.get('ANTHROPIC_API_KEY_SECRET_NAME')
        if not secret_name:
            raise ValueError("ANTHROPIC_API_KEY_SECRET_NAME environment variable is not set")
        
        response = secretsmanager.get_secret_value(SecretId=secret_name)
        secret = json.loads(response['SecretString'])
        return secret['anthropicApiKey']
    except Exception as e:
        logger.error(f"Error retrieving Anthropic API key: {str(e)}")
        raise

def generate_research_structure(topic: str) -> Dict[str, Any]:
    """
    Generate research questions and outline for a given topic using Anthropic API.
    
    Args:
        topic: The research topic to analyze
        
    Returns:
        A dictionary containing subtopics, research questions, and confidence scores
    """
    try:
        # Get Anthropic API key
        api_key = get_anthropic_api_key()
        
        # Initialize Anthropic client
        client = anthropic.Anthropic(api_key=api_key)
        
        # Create the prompt for Claude
        prompt = f"""
        I need to create a structured research plan for the topic: "{topic}".
        
        Please analyze this topic and:
        1. Break it down into 3-5 key subtopics that provide comprehensive coverage
        2. For each subtopic, generate 2-3 specific research questions
        3. Assign a confidence score (0.0-1.0) to each question based on how relevant and well-defined it is
        
        Format your response as a JSON object with this structure:
        {{
            "topic": "the original topic",
            "subtopics": [
                {{
                    "name": "subtopic name",
                    "description": "brief description of this subtopic",
                    "questions": [
                        {{
                            "question": "specific research question",
                            "confidence": 0.95,
                            "rationale": "brief explanation of why this question is important"
                        }}
                    ]
                }}
            ]
        }}
        
        Only return the JSON object, nothing else.
        """
        
        # Call Anthropic API
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=2000,
            temperature=0.2,
            system="You are a research planning assistant that helps break down topics into structured research questions. Always return valid JSON.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract and parse the JSON response
        content = response.content[0].text
        # Remove any markdown code block indicators if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        result = json.loads(content)
        
        # Add metadata
        result["metadata"] = {
            "model": "claude-3-sonnet-20240229",
            "generated_at": response.id,
            "token_count": response.usage.input_tokens + response.usage.output_tokens
        }
        
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON response: {str(e)}")
        logger.error(f"Raw response: {content}")
        raise ValueError("Failed to parse response from Anthropic API")
    except Exception as e:
        logger.error(f"Error generating research structure: {str(e)}")
        raise

def validate_topic(topic: str) -> Optional[str]:
    """
    Validate the input topic and return an error message if invalid.
    
    Args:
        topic: The topic to validate
        
    Returns:
        Error message if invalid, None if valid
    """
    if not topic:
        return "Topic cannot be empty"
    
    if len(topic) < 5:
        return "Topic is too short. Please provide a more descriptive topic."
    
    if len(topic) > 200:
        return "Topic is too long. Please provide a more concise topic."
    
    return None

def lambda_handler(event, context):
    """
    AWS Lambda handler function.
    
    Args:
        event: The event dict from AWS Lambda
        context: The context object from AWS Lambda
        
    Returns:
        API Gateway response with research structure or error
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Extract topic from event
        if 'body' in event:
            # Handle API Gateway request
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
            topic = body.get('topic', '')
        else:
            # Handle direct Lambda invocation
            topic = event.get('topic', '')
        
        # Validate topic
        error = validate_topic(topic)
        if error:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': error
                })
            }
        
        # Generate research structure
        result = generate_research_structure(topic)
        
        # Return successful response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        
        # Return error response
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f"Internal server error: {str(e)}"
            })
        } 