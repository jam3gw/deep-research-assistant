import json
import os
import boto3
import logging
import uuid

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    """
    Main Lambda handler function for AWS Connect integration
    
    This function handles incoming requests from AWS Connect, processes them,
    and returns responses suitable for text-to-speech in the call flow.
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Extract the caller's input from the Connect event
        # The exact structure depends on how Connect is configured
        caller_input = extract_caller_input(event)
        
        if not caller_input:
            return generate_response("I didn't catch that. Could you please repeat?")
        
        # Get or create a conversation ID for this call
        conversation_id = event.get('Details', {}).get('ContactData', {}).get('ContactId', str(uuid.uuid4()))
        
        # Call the conversation handler Lambda to process the input
        conversation_handler_response = invoke_conversation_handler(caller_input, conversation_id)
        
        # Extract the SSML response from the conversation handler
        ssml_response = extract_ssml_response(conversation_handler_response)
        
        # Return the response in a format suitable for Connect
        return generate_response(ssml_response)
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return generate_response(
            "<speak>I'm sorry, I encountered an error and couldn't process your request. Please try again later.</speak>"
        )

def extract_caller_input(event):
    """
    Extracts the caller's input from the Connect event
    """
    # The exact path to the caller input depends on your Connect contact flow configuration
    # This is a common pattern, but you may need to adjust based on your specific setup
    try:
        # Try to get input from stored customer input
        if 'Details' in event and 'Parameters' in event['Details']:
            parameters = event['Details']['Parameters']
            
            # Check for speech input
            if 'SpeechResult' in parameters:
                return parameters['SpeechResult']
                
            # Check for DTMF (keypad) input
            if 'Digits' in parameters:
                return parameters['Digits']
        
        # If we can't find input in the expected places, log the event structure for debugging
        logger.warning(f"Could not find caller input in event: {json.dumps(event)}")
        return None
    except Exception as e:
        logger.error(f"Error extracting caller input: {str(e)}")
        return None

def invoke_conversation_handler(prompt, conversation_id):
    """
    Invokes the conversation handler Lambda function
    """
    function_name = os.environ.get('CONVERSATION_HANDLER_FUNCTION_NAME')
    
    payload = {
        'prompt': prompt,
        'conversationId': conversation_id
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        response_payload = json.loads(response['Payload'].read().decode('utf-8'))
        logger.info(f"Conversation handler response: {json.dumps(response_payload)}")
        
        return response_payload
    except Exception as e:
        logger.error(f"Error invoking conversation handler: {str(e)}")
        raise

def extract_ssml_response(response):
    """
    Extracts the SSML response from the conversation handler response
    """
    try:
        # Check if the response has the expected structure
        if 'body' in response and 'ssml' in response['body']:
            return response['body']['ssml']
        
        # If not, try to find the SSML in other common locations
        if 'ssml' in response:
            return response['ssml']
            
        if isinstance(response, dict) and 'body' in response:
            body = response['body']
            if isinstance(body, str):
                try:
                    body_json = json.loads(body)
                    if 'ssml' in body_json:
                        return body_json['ssml']
                except:
                    pass
        
        # If we can't find SSML, return a default message
        logger.warning(f"Could not find SSML in response: {json.dumps(response)}")
        return "<speak>I processed your request, but couldn't generate a proper response. Please try again.</speak>"
    except Exception as e:
        logger.error(f"Error extracting SSML response: {str(e)}")
        return "<speak>I encountered an error while processing your request. Please try again later.</speak>"

def generate_response(ssml_text):
    """
    Generates a response suitable for AWS Connect
    """
    return {
        'statusCode': 200,
        'type': 'ssml',
        'text': ssml_text,
        'keepPrompt': True  # This tells Connect to keep the prompt active for further interaction
    } 