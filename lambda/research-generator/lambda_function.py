"""
Main Lambda function handler for the research generator.
"""
import json
import boto3
import os
from anthropic import Anthropic
import openai
from rag_engine import RAGEngine, deduplicate_sources
from utils import build_response
import time
import traceback

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
            start_time = time.time()
            try:
                print(f"Starting answer generation for query: '{query}'")
                question_tree = rag.generate_answer_with_tree(query, client, brave_key)
                print("Answer generation completed successfully")
            except Exception as e:
                print(f"ERROR during answer generation: {str(e)}")
                print(f"Exception type: {type(e).__name__}")
                print(f"Exception traceback: {traceback.format_exc()}")
                raise ValueError(f"Failed to generate answer: {str(e)}")
                
            processing_time = time.time() - start_time
            print(f"Total processing time: {processing_time:.2f} seconds")
            
            # Log the question tree structure for debugging
            print("Generated question tree structure:")
            try:
                print(json.dumps(question_tree, indent=2, default=str))
            except Exception as e:
                print(f"ERROR serializing question tree: {str(e)}")
                print(f"Question tree type: {type(question_tree)}")
                print(f"Question tree keys: {question_tree.keys() if isinstance(question_tree, dict) else 'Not a dict'}")
            
            # Verify if answer exists in the question tree
            if isinstance(question_tree, dict) and 'answer' not in question_tree:
                print("WARNING: Root node is missing 'answer' field")
                print(f"Available fields in root node: {list(question_tree.keys())}")
                
                # Check if there was an error message in the question tree
                if 'error' in question_tree:
                    print(f"Error found in question tree: {question_tree['error']}")
                    raise ValueError(f"Error in answer generation: {question_tree['error']}")
            elif not isinstance(question_tree, dict):
                print(f"WARNING: Question tree is not a dictionary. Type: {type(question_tree)}")
                raise ValueError("Invalid question tree structure returned")
            else:
                print(f"Answer field exists in root node, length: {len(question_tree.get('answer', ''))}")
            
            # Collect all sources from the tree
            all_sources = collect_all_sources(question_tree)
            
            # If there's a breakdown, use the final answer from the root node
            if question_tree.get('needs_breakdown', False) and question_tree.get('children'):
                final_answer = question_tree.get('answer', "No answer was generated. Please try again with a more specific question.")
                
                # Check if sources section is missing and add it if necessary
                if all_sources:
                    # Instead of adding sources to the HTML, we'll include them in the response JSON
                    # The frontend will handle displaying the sources
                    pass
            else:
                # If no breakdown, use the direct answer
                final_answer = question_tree.get('answer', "No answer was generated. Please try again with a more specific question.")
            
            # Calculate metadata for the frontend
            metadata = {
                'total_nodes': count_nodes(question_tree),
                'max_depth': get_max_depth(question_tree),
                'processing_time': f"{processing_time:.2f} seconds"
            }
            
            # Include all sources in the response for the frontend to handle
            response = {
                'explanation': final_answer,
                'question_tree': question_tree,
                'metadata': metadata,
                'all_sources': all_sources,
                'sources_metadata': {
                    'total_sources': len(all_sources),
                    'sources_by_relevance': sorted(all_sources, key=lambda s: -s.get('relevance', 0)),
                    'most_frequent_sources': sorted(all_sources, key=lambda s: -s.get('frequency', 0))[:5]
                }
            }
            
            return build_response(200, response, not is_function_url)
            
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

def collect_all_sources(tree):
    """Collect all sources from the tree with frequency and relevance information."""
    sources = []
    source_frequency = {}  # Track how many times each source appears
    
    # Helper function to recursively collect sources with depth information
    def _collect_sources_with_depth(node, depth=0):
        if not node or not isinstance(node, dict):
            print(f"WARNING: Invalid node at depth {depth}: {type(node)}")
            return []
            
        node_sources = []
        
        # Collect sources from the current node if available
        if 'sources' in node and node['sources']:
            try:
                for source in node['sources']:
                    if not isinstance(source, dict):
                        print(f"WARNING: Invalid source type: {type(source)}")
                        continue
                        
                    # Create a copy of the source with depth information
                    source_with_depth = source.copy()
                    source_with_depth['depth'] = depth
                    source_with_depth['node_question'] = node.get('question', '')
                    node_sources.append(source_with_depth)
                    
                    # Track frequency
                    url = source.get('url', '')
                    if url:
                        source_frequency[url] = source_frequency.get(url, 0) + 1
            except Exception as e:
                print(f"ERROR processing sources at depth {depth}: {str(e)}")
        
        # Recursively collect sources from children
        if 'children' in node and node['children']:
            try:
                for child in node['children']:
                    child_sources = _collect_sources_with_depth(child, depth + 1)
                    if child_sources:
                        node_sources.extend(child_sources)
            except Exception as e:
                print(f"ERROR processing children at depth {depth}: {str(e)}")
        
        return node_sources
    
    try:
        # Collect all sources with depth information
        sources = _collect_sources_with_depth(tree)
        
        # Deduplicate sources while preserving the most relevant information
        deduplicated_sources = []
        seen_urls = set()
        
        # Sort sources by frequency (most frequent first) and then by depth (lower depth first)
        sources.sort(key=lambda s: (-source_frequency.get(s.get('url', ''), 0), s.get('depth', 0)))
        
        for source in sources:
            url = source.get('url', '')
            if url and url not in seen_urls:
                # Add frequency information
                source['frequency'] = source_frequency.get(url, 1)
                # Calculate relevance score (higher is more relevant)
                source['relevance'] = (source['frequency'] * 10) / (source.get('depth', 0) + 1)
                deduplicated_sources.append(source)
                seen_urls.add(url)
        
        return deduplicated_sources
    except Exception as e:
        print(f"ERROR in collect_all_sources: {str(e)}")
        # Return an empty list in case of error
        return []