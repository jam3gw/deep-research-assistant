"""
Main Lambda function handler for the research generator.
"""
import json
import boto3
import os
import uuid
import asyncio
from anthropic import Anthropic

# Import modules
from config import (
    MAX_ALLOWED_RECURSION_DEPTH, MAX_ALLOWED_SUB_QUESTIONS,
    DEFAULT_RECURSION_DEPTH, DEFAULT_SUB_QUESTIONS, DEFAULT_RECURSION_THRESHOLD
)
from utils import build_response
from question_processor import process_question_node
from answer_aggregator import aggregate_answers, aggregate_answers_async
from tree_visualizer import generate_tree_visualization

def lambda_handler(event, context):
    # Check if this is a Lambda Function URL invocation (it will have 'requestContext.http' in the event)
    is_function_url = 'requestContext' in event and 'http' in event.get('requestContext', {})
    
    # Handle preflight OPTIONS request
    if event.get('httpMethod') == 'OPTIONS':
        return build_response(200, {}, not is_function_url)
    
    # Get the parameter name from environment variables
    parameter_name = os.environ['ANTHROPIC_API_KEY_SECRET_NAME']
    
    session = boto3.session.Session()
    ssm_client = session.client('ssm')
    
    try:
        print(f"Attempting to get parameter: {parameter_name}")
        response = ssm_client.get_parameter(
            Name=parameter_name,
            WithDecryption=True
        )
        
        api_key = response['Parameter']['Value']
        
        # Log key details safely for debugging
        key_length = len(api_key) if api_key else 0
        key_prefix = api_key[:4] if key_length >= 4 else api_key
        key_suffix = api_key[-4:] if key_length >= 8 else ""
        print(f"API Key retrieved - Length: {key_length}, Prefix: {key_prefix}, Suffix: {key_suffix}")
        print(f"API Key format check - Starts with 'sk-ant-': {api_key.startswith('sk-ant-') if api_key else False}")
        
        # Initialize Anthropic client
        client = Anthropic(api_key=api_key)
        print("Successfully initialized Anthropic client")

        # Parse the incoming event
        try:
            body = json.loads(event.get('body', '{}'))
            main_question = body.get('expression')
            
            if not main_question:
                return build_response(400, {
                    'error': 'Missing required parameter. Please provide a research topic.'
                }, not is_function_url)

            # Get user-specified parameters with validation
            max_recursion_depth = min(
                int(body.get('max_recursion_depth', DEFAULT_RECURSION_DEPTH)), 
                MAX_ALLOWED_RECURSION_DEPTH
            )
            max_sub_questions = min(
                int(body.get('max_sub_questions', DEFAULT_SUB_QUESTIONS)), 
                MAX_ALLOWED_SUB_QUESTIONS
            )
            recursion_threshold = min(
                int(body.get('recursion_threshold', DEFAULT_RECURSION_THRESHOLD)), 
                2  # Maximum threshold value is 2
            )
            
            # Ensure values are within valid ranges
            max_recursion_depth = max(0, max_recursion_depth)
            max_sub_questions = max(1, max_sub_questions)
            recursion_threshold = max(0, recursion_threshold)
            
            print(f"Processing main question: {main_question}")
            print(f"Using parameters - max_recursion_depth: {max_recursion_depth}, " +
                  f"max_sub_questions: {max_sub_questions}, recursion_threshold: {recursion_threshold}")
            
            # Start the recursive question breakdown and answering process
            question_tree = {
                'id': str(uuid.uuid4()),
                'question': main_question,
                'depth': 0,
                'children': []
            }
            
            # Process the question tree recursively with user-specified parameters
            # The process_question_node function now handles setting up the event loop internally
            process_question_node(
                question_tree, 
                client, 
                max_recursion_depth=max_recursion_depth,
                max_sub_questions=max_sub_questions,
                recursion_threshold=recursion_threshold
            )
            
            # Generate the final aggregated answer
            # Create a new event loop for the aggregation step
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                final_answer = loop.run_until_complete(aggregate_answers_async(question_tree, client))
            finally:
                loop.close()
            
            # Generate a visualization of the thought tree
            tree_visualization = generate_tree_visualization(question_tree)
            
            # Include the parameters used in the response
            return build_response(200, {
                'explanation': final_answer,
                'tree_visualization': tree_visualization,
                'question_tree': question_tree,
                'parameters_used': {
                    'max_recursion_depth': max_recursion_depth,
                    'max_sub_questions': max_sub_questions,
                    'recursion_threshold': recursion_threshold
                },
                'success': True,
                'formatted': True
            }, not is_function_url)
            
        except json.JSONDecodeError:
            return build_response(400, {'error': 'Invalid JSON in request body'}, not is_function_url)
        except ValueError as ve:
            return build_response(400, {'error': f'Invalid parameter value: {str(ve)}'}, not is_function_url)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        return build_response(500, {'error': f'Internal server error: {str(e)}'}, not is_function_url)