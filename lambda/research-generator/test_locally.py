#!/usr/bin/env python3
"""
Test script for the RAG-based research generator locally.
This allows you to test the function before deploying to AWS Lambda.

Usage:
    python test_locally.py "What is the current state of quantum computing?"
"""

import os
import json
import argparse
import time
from anthropic import Anthropic
import openai
from rag_engine import RAGEngine
from tree_visualizer import validate_tree_structure
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_environment():
    """Set up environment variables and API clients."""
    # Check for required API keys
    if 'ANTHROPIC_API_KEY' not in os.environ:
        raise ValueError("Please set ANTHROPIC_API_KEY environment variable")
    if 'OPENAI_API_KEY' not in os.environ:
        raise ValueError("Please set OPENAI_API_KEY environment variable")
    if 'BRAVE_API_KEY' not in os.environ:
        raise ValueError("Please set BRAVE_API_KEY environment variable")
    
    # Initialize clients
    client = Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
    openai.api_key = os.environ['OPENAI_API_KEY']
    brave_key = os.environ['BRAVE_API_KEY']
    
    return client, brave_key

def print_tree_structure(node, indent=0):
    """Print the question tree structure in a readable format."""
    prefix = "  " * indent
    print(f"\n{prefix}Question: {node['question']}")
    
    if node.get('answer'):
        # Split answer into lines for better readability
        answer_lines = node['answer'].split('\n')
        print(f"{prefix}Answer:")
        for line in answer_lines:
            print(f"{prefix}  {line}")
    
    if node.get('children'):
        print(f"{prefix}Sub-questions:")
        for child in node['children']:
            print_tree_structure(child, indent + 1)

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

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test the RAG-based research generator locally.')
    parser.add_argument('question', type=str, help='The research question to process')
    args = parser.parse_args()
    
    # Start timing
    start_time = time.time()
    
    try:
        # Set up environment and clients
        client, brave_key = setup_environment()
        
        print(f"\nProcessing question: {args.question}")
        print("\n--- Starting RAG Process ---")
        
        # Initialize RAG engine
        rag = RAGEngine()
        
        # Set OpenAI API key
        rag.set_openai_key(os.environ['OPENAI_API_KEY'])
        
        # Generate answer with question tree
        print("\nGenerating question tree and answers...")
        try:
            question_tree = rag.generate_answer_with_tree(args.question, client, brave_key)

            print("Generated question tree structure:")
            print(json.dumps(question_tree, indent=2, default=str))
            
            # Validate the tree structure
            is_valid, issues = validate_tree_structure(question_tree)
            if not is_valid:
                print("\nWARNING: Tree structure validation failed with the following issues:")
                for issue in issues:
                    print(f"  - {issue}")
                print("Attempting to continue anyway...")
                
        except Exception as e:
            logger.error(f"Error generating question tree: {str(e)}")
            raise
        
        # Get final answer
        print("\nGenerating final synthesized answer...")
        try:
            if question_tree.get('needs_breakdown', False):
                # If tree was broken down, use the last answer as final
                final_answer = rag.generate_answer(args.question, client, brave_key)
                sources = []  # Since generate_answer doesn't return sources, initialize as empty
            else:
                # If no breakdown, use the direct answer
                final_answer = question_tree['answer']
                sources = question_tree.get('sources', [])
        except Exception as e:
            logger.error(f"Error generating final answer: {str(e)}")
            raise
        
        # Calculate metadata
        execution_time = time.time() - start_time
        metadata = {
            'total_nodes': count_nodes(question_tree),
            'max_depth': get_max_depth(question_tree),
            'processing_time': f"{execution_time:.2f} seconds"
        }
        
        # Print results
        print("\n=== Question Tree Structure ===")
        print_tree_structure(question_tree)
        
        print("\n=== Final Answer ===")
        print(final_answer)
        
        print("\n=== Sources ===")
        for i, source in enumerate(sources, 1):
            print(f"{i}. {source.get('title', 'Untitled')} - {source.get('url', 'No URL')}")
            
        print("\n=== Metadata ===")
        print(f"Total nodes: {metadata['total_nodes']}")
        print(f"Maximum depth: {metadata['max_depth']}")
        print(f"Processing time: {metadata['processing_time']}")
        
        # Save output
        output = {
            'explanation': final_answer,
            'question_tree': question_tree,
            'sources': sources,
            'metadata': metadata,
            'execution_time': execution_time
        }
        
        os.makedirs('output', exist_ok=True)
        with open('output/last_run.json', 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\nExecution completed in {execution_time:.2f} seconds")
        print("Results saved to output/last_run.json")
        print("Note: Tree visualization is now generated client-side")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        raise

if __name__ == '__main__':
    main() 