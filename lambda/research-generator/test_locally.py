#!/usr/bin/env python3
"""
Test script for the research generator Lambda function with recursive question breakdown.
This allows you to test the function locally before deploying to AWS.

Usage:
    python test_locally.py "What are the economic and environmental impacts of renewable energy adoption globally?"
    python test_locally.py --threshold 2 "What are the economic and environmental impacts of renewable energy adoption globally?"
    python test_locally.py --depth 3 --sub-questions 4 --threshold 1 "What are the economic and environmental impacts of renewable energy adoption globally?"
"""

import sys
import json
import os
import uuid
import argparse
from anthropic import Anthropic

# Import from the refactored modules
from config import (
    MAX_ALLOWED_RECURSION_DEPTH,
    MAX_ALLOWED_SUB_QUESTIONS,
    DEFAULT_RECURSION_DEPTH,
    DEFAULT_SUB_QUESTIONS,
    DEFAULT_RECURSION_THRESHOLD
)
from question_processor import (
    process_question_node,
    should_break_down_question
)
from answer_generator import get_answer_for_question
from answer_aggregator import aggregate_answers
from tree_visualizer import generate_tree_visualization
from utils import extract_content

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test the research generator with recursive question breakdown.')
    parser.add_argument('question', type=str, help='The research question to process')
    parser.add_argument('--threshold', '-t', type=int, choices=[0, 1, 2], default=DEFAULT_RECURSION_THRESHOLD, 
                        help=f'Recursion threshold (0=normal, 1=conservative, 2=very conservative). Default: {DEFAULT_RECURSION_THRESHOLD}')
    parser.add_argument('--depth', '-d', type=int, default=DEFAULT_RECURSION_DEPTH, 
                        help=f'Maximum recursion depth (0-{MAX_ALLOWED_RECURSION_DEPTH}). Default: {DEFAULT_RECURSION_DEPTH}')
    parser.add_argument('--sub-questions', '-s', type=int, default=DEFAULT_SUB_QUESTIONS, 
                        help=f'Maximum number of sub-questions (1-{MAX_ALLOWED_SUB_QUESTIONS}). Default: {DEFAULT_SUB_QUESTIONS}')
    args = parser.parse_args()
    
    # Validate parameters
    max_recursion_depth = min(max(0, args.depth), MAX_ALLOWED_RECURSION_DEPTH)
    max_sub_questions = min(max(1, args.sub_questions), MAX_ALLOWED_SUB_QUESTIONS)
    recursion_threshold = args.threshold
    
    # Get the question from command line arguments
    main_question = args.question
    print(f"Processing research question: {main_question}")
    print(f"Parameters: max_recursion_depth={max_recursion_depth}, max_sub_questions={max_sub_questions}, recursion_threshold={recursion_threshold}")
    
    # Set environment variables (you'll need to set your API key)
    if 'ANTHROPIC_API_KEY' not in os.environ:
        print("Please set the ANTHROPIC_API_KEY environment variable")
        print("Example: export ANTHROPIC_API_KEY=your_api_key")
        sys.exit(1)
    
    api_key = os.environ['ANTHROPIC_API_KEY']
    
    try:
        # Initialize Anthropic client
        print("Initializing Anthropic client...")
        client = Anthropic(api_key=api_key)
        
        # Start the recursive question breakdown and answering process
        print("\n--- Starting Question Breakdown Process ---")
        question_tree = {
            'id': str(uuid.uuid4()),
            'question': main_question,
            'depth': 0,
            'children': []
        }
        
        # Process the question tree recursively with user-specified parameters
        process_question_node(
            question_tree, 
            client, 
            max_recursion_depth=max_recursion_depth,
            max_sub_questions=max_sub_questions,
            recursion_threshold=recursion_threshold
        )
        
        # Print the question tree structure
        print("\n--- Question Tree Structure ---")
        print_tree_structure(question_tree)
        
        # Generate the final aggregated answer
        print("\n--- Generating Final Answer ---")
        final_answer = aggregate_answers(question_tree, client)
        
        # Generate a visualization of the thought tree
        tree_visualization = generate_tree_visualization(question_tree)
        
        # Print the result
        print("\n--- Final Research Answer ---")
        print(final_answer)
        
        # Save to files
        output_dir = "research_output"
        os.makedirs(output_dir, exist_ok=True)
        
        # Save the question tree
        with open(f"{output_dir}/question_tree.json", "w") as f:
            json.dump(question_tree, f, indent=2)
        print(f"\nQuestion tree saved to {output_dir}/question_tree.json")
        
        # Save the final answer
        with open(f"{output_dir}/final_answer.html", "w") as f:
            f.write(final_answer)
        print(f"Final answer saved to {output_dir}/final_answer.html")
        
        # Save the tree visualization
        with open(f"{output_dir}/tree_visualization.html", "w") as f:
            f.write(tree_visualization)
        print(f"Tree visualization saved to {output_dir}/tree_visualization.html")
        
        # Save the complete output
        complete_output = {
            'explanation': final_answer,
            'tree_visualization': tree_visualization,
            'question_tree': question_tree,
            'parameters_used': {
                'max_recursion_depth': max_recursion_depth,
                'max_sub_questions': max_sub_questions,
                'recursion_threshold': recursion_threshold
            }
        }
        with open(f"{output_dir}/complete_output.json", "w") as f:
            json.dump(complete_output, f, indent=2)
        print(f"Complete output saved to {output_dir}/complete_output.json")
        
    except Exception as e:
        import traceback
        print(f"Error processing research question: {str(e)}")
        print("Full traceback:")
        traceback.print_exc()
        sys.exit(1)

def print_tree_structure(node, indent=0):
    """
    Print the question tree structure in a readable format
    """
    prefix = "  " * indent
    print(f"{prefix}Question: {node['question']}")
    
    if node.get('needs_breakdown', False):
        print(f"{prefix}Broken down into {len(node['children'])} sub-questions:")
        for child in node['children']:
            print_tree_structure(child, indent + 1)
    else:
        if 'answer' in node:
            answer_preview = node['answer'][:100] + "..." if len(node['answer']) > 100 else node['answer']
            print(f"{prefix}Answer: {answer_preview}")
        else:
            print(f"{prefix}No answer yet")

if __name__ == "__main__":
    main() 