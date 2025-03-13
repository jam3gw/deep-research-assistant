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
from tree_visualizer import generate_tree_visualization, validate_tree_structure
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
        
        # Generate tree visualization
        print("\nGenerating tree visualization...")
        try:
            tree_visualization = generate_tree_visualization(question_tree)
        except Exception as e:
            logger.error(f"Error generating tree visualization: {str(e)}")
            tree_visualization = "Error generating visualization"
        
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
        
        # Print results
        print("\n=== Question Tree Structure ===")
        print_tree_structure(question_tree)
        
        print("\n=== Final Answer ===")
        print(final_answer)
        
        print("\n=== Sources ===")
        for i, source in enumerate(sources, 1):
            print(f"{i}. {source.get('title', 'Untitled')} - {source.get('url', 'No URL')}")
        
        # Save output
        output = {
            'explanation': final_answer,
            'tree_visualization': tree_visualization,
            'question_tree': question_tree,
            'sources': sources,
            'execution_time': time.time() - start_time
        }
        
        os.makedirs('output', exist_ok=True)
        with open('output/last_run.json', 'w') as f:
            json.dump(output, f, indent=2)
            
        # Save tree visualization to a separate HTML file for easy viewing
        with open('output/tree.html', 'w') as f:
            f.write(tree_visualization)
        
        print(f"\nExecution completed in {time.time() - start_time:.2f} seconds")
        print("Results saved to output/last_run.json")
        print("Tree visualization saved to output/tree.html")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        raise

if __name__ == '__main__':
    main() 