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
import time
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

def clean_tree_for_serialization(node):
    """
    Clean the question tree to remove any non-serializable objects.
    Returns a new tree that can be safely serialized to JSON.
    """
    # Create a new node with only serializable fields
    clean_node = {}
    
    # Copy all serializable fields
    for key, value in node.items():
        # Skip keys that start with underscore (private fields)
        if key.startswith('_'):
            continue
        
        # Handle children recursively
        if key == 'children' and isinstance(value, list):
            clean_node[key] = [clean_tree_for_serialization(child) for child in value]
        else:
            # Include all other fields
            clean_node[key] = value
    
    return clean_node

def main():
    # Start the timer for the entire process
    start_time_total = time.time()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test the research generator with recursive question breakdown.')
    parser.add_argument('question', type=str, help='The research question to process')
    parser.add_argument('--threshold', '-t', type=int, choices=[0, 1, 2], default=DEFAULT_RECURSION_THRESHOLD, 
                        help=f'Recursion threshold (0=normal, 1=conservative, 2=very conservative). Default: {DEFAULT_RECURSION_THRESHOLD}')
    parser.add_argument('--depth', '-d', type=int, default=DEFAULT_RECURSION_DEPTH, 
                        help=f'Maximum recursion depth (0-{MAX_ALLOWED_RECURSION_DEPTH}). Default: {DEFAULT_RECURSION_DEPTH}')
    parser.add_argument('--sub-questions', '-s', type=int, default=DEFAULT_SUB_QUESTIONS, 
                        help=f'Maximum number of sub-questions (1-{MAX_ALLOWED_SUB_QUESTIONS}). Default: {DEFAULT_SUB_QUESTIONS}')
    parser.add_argument('--skip-visualization', action='store_true', help='Skip generating tree visualization to save time')
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
        step_start_time = time.time()
        
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
        
        step_end_time = time.time()
        question_breakdown_time = step_end_time - step_start_time
        print(f"Question breakdown completed in {question_breakdown_time:.2f} seconds")
        
        # Clean the question tree for serialization
        clean_question_tree = clean_tree_for_serialization(question_tree)
        
        # Print the question tree structure
        print("\n--- Question Tree Structure ---")
        print_tree_structure(clean_question_tree)
        
        # Generate the final aggregated answer
        print("\n--- Generating Final Answer ---")
        step_start_time = time.time()
        
        final_answer = aggregate_answers(question_tree, client)
        
        step_end_time = time.time()
        answer_aggregation_time = step_end_time - step_start_time
        print(f"Answer aggregation completed in {answer_aggregation_time:.2f} seconds")
        
        # Generate a visualization of the thought tree (optional)
        visualization_time = 0
        tree_visualization = ""
        
        if not args.skip_visualization:
            print("\n--- Generating Tree Visualization ---")
            step_start_time = time.time()
            
            tree_visualization = generate_tree_visualization(clean_question_tree)
            
            step_end_time = time.time()
            visualization_time = step_end_time - step_start_time
            print(f"Tree visualization completed in {visualization_time:.2f} seconds")
        else:
            print("\n--- Skipping Tree Visualization ---")
            tree_visualization = "<p>Tree visualization was skipped to save time.</p>"
        
        # Print the result
        print("\n--- Final Research Answer ---")
        # Print a simplified version of the answer (without HTML tags)
        simplified_answer = final_answer.replace('<div class="research-answer">', '').replace('</div>', '')
        simplified_answer = simplified_answer.replace('<style>', '').split('</style>')[-1]
        print(simplified_answer[:500] + "..." if len(simplified_answer) > 500 else simplified_answer)
        
        # Save to files
        print("\n--- Saving Output Files ---")
        step_start_time = time.time()
        
        output_dir = "research_output"
        os.makedirs(output_dir, exist_ok=True)
        
        # Save the question tree
        with open(f"{output_dir}/question_tree.json", "w") as f:
            json.dump(clean_question_tree, f, indent=2)
        print(f"\nQuestion tree saved to {output_dir}/question_tree.json")
        
        # Save the final answer
        with open(f"{output_dir}/final_answer.html", "w") as f:
            f.write(final_answer)
        print(f"Final answer saved to {output_dir}/final_answer.html")
        
        # Save the tree visualization if it was generated
        if not args.skip_visualization:
            with open(f"{output_dir}/tree_visualization.html", "w") as f:
                f.write(tree_visualization)
            print(f"Tree visualization saved to {output_dir}/tree_visualization.html")
        
        # Save the complete output
        complete_output = {
            'explanation': final_answer,
            'tree_visualization': tree_visualization,
            'question_tree': clean_question_tree,
            'parameters_used': {
                'max_recursion_depth': max_recursion_depth,
                'max_sub_questions': max_sub_questions,
                'recursion_threshold': recursion_threshold
            },
            'timing_info': {
                'question_breakdown_time': question_breakdown_time,
                'answer_aggregation_time': answer_aggregation_time,
                'visualization_time': visualization_time,
                'total_time': time.time() - start_time_total
            }
        }
        with open(f"{output_dir}/complete_output.json", "w") as f:
            json.dump(complete_output, f, indent=2)
        print(f"Complete output saved to {output_dir}/complete_output.json")
        
        step_end_time = time.time()
        saving_time = step_end_time - step_start_time
        print(f"Output files saved in {saving_time:.2f} seconds")
        
        # Calculate and display the total execution time
        end_time_total = time.time()
        total_time = end_time_total - start_time_total
        
        print("\n--- Execution Time Summary ---")
        print(f"Question breakdown:  {question_breakdown_time:.2f} seconds")
        print(f"Answer aggregation:  {answer_aggregation_time:.2f} seconds")
        print(f"Tree visualization:  {visualization_time:.2f} seconds")
        print(f"Saving output files: {saving_time:.2f} seconds")
        print(f"Total execution time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
        
    except Exception as e:
        import traceback
        print(f"Error processing research question: {str(e)}")
        print("Full traceback:")
        traceback.print_exc()
        
        # Even if there's an error, show how much time has elapsed
        end_time_total = time.time()
        total_time = end_time_total - start_time_total
        print(f"\nExecution failed after {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
        
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