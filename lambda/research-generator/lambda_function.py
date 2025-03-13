"""
Main Lambda function handler for the research generator.
"""
import json
import boto3
import os
from anthropic import Anthropic
import openai
from rag_engine import RAGEngine
from utils import build_response

def lambda_handler(event, context):
    # Check if this is a Lambda Function URL invocation
    is_function_url = 'requestContext' in event and 'http' in event.get('requestContext', {})
    
    # Handle preflight OPTIONS request
    if event.get('httpMethod') == 'OPTIONS':
        return build_response(200, {}, not is_function_url)
    
    # Get API keys from environment variables
    anthropic_key_name = os.environ['ANTHROPIC_API_KEY_SECRET_NAME']
    openai_key_name = os.environ['OPENAI_API_KEY_SECRET_NAME']
    brave_key_name = os.environ['BRAVE_API_KEY_SECRET_NAME']
    
    session = boto3.session.Session()
    ssm_client = session.client('ssm')
    
    try:
        # Get API keys from SSM
        anthropic_key = ssm_client.get_parameter(
            Name=anthropic_key_name,
            WithDecryption=True
        )['Parameter']['Value']
        
        openai_key = ssm_client.get_parameter(
            Name=openai_key_name,
            WithDecryption=True
        )['Parameter']['Value']
        
        brave_key = ssm_client.get_parameter(
            Name=brave_key_name,
            WithDecryption=True
        )['Parameter']['Value']
        
        # Initialize clients
        client = Anthropic(api_key=anthropic_key)
        
        # Parse the incoming event
        try:
            body = json.loads(event.get('body', '{}'))
            query = body.get('expression')
            
            if not query:
                return build_response(400, {
                    'error': 'Missing required parameter. Please provide a research topic.'
                }, not is_function_url)
            
            # Initialize RAG engine
            rag = RAGEngine()
            # Set OpenAI API key
            rag.set_openai_key(openai_key)
            
            # Generate answer with question tree using dynamic knowledge base
            question_tree = rag.generate_answer_with_tree(query, client, brave_key)

            # Log the question tree structure for debugging
            print("Generated question tree structure:")
            print(json.dumps(question_tree, indent=2, default=str))
            
            # Get the final answer from the tree structure
            if question_tree['needs_breakdown']:
                # If tree was broken down, use the last answer as final
                final_answer = rag.generate_answer(query, client, brave_key, depth=0)
            else:
                # If no breakdown, use the direct answer
                final_answer = question_tree['answer']
            
            # Calculate metadata for the frontend
            metadata = {
                'total_nodes': count_nodes(question_tree),
                'max_depth': get_max_depth(question_tree),
                'processing_time': 'N/A'  # Could add actual processing time if needed
            }
            
            # Return the response with tree structure but without HTML visualization
            return build_response(200, {
                'explanation': final_answer,
                'question_tree': question_tree,
                'metadata': metadata,
                'success': True,
                'formatted': True
            }, not is_function_url)
            
        except json.JSONDecodeError:
            return build_response(400, {'error': 'Invalid JSON in request body'}, not is_function_url)
        except ValueError as ve:
            return build_response(400, {'error': f'Invalid parameter value: {str(ve)}'}, not is_function_url)
        except Exception as e:
            return build_response(500, {'error': f'Internal server error: {str(e)}'}, not is_function_url)
            
    except Exception as e:
        return build_response(500, {'error': f'Error retrieving API keys: {str(e)}'}, not is_function_url)

def count_nodes(tree):
    """Count the total number of nodes in the tree."""
    if not tree:
        return 0
    
    count = 1  # Count the current node
    
    # Add count of all children
    if 'children' in tree and tree['children']:
        for child in tree['children']:
            count += count_nodes(child)
    
    return count

def get_max_depth(tree, current_depth=0):
    """Get the maximum depth of the tree."""
    if not tree:
        return current_depth
    
    max_depth = current_depth
    
    # Check all children for their max depth
    if 'children' in tree and tree['children']:
        for child in tree['children']:
            child_depth = get_max_depth(child, current_depth + 1)
            max_depth = max(max_depth, child_depth)
    
    return max_depth