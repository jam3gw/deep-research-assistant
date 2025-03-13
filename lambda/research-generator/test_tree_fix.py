#!/usr/bin/env python3
"""
Test script to verify the tree visualization fixes.
This creates a tree structure similar to the one in the logs and generates a visualization.
"""

import os
import json
import uuid
from tree_visualizer import generate_tree_visualization

def create_test_tree():
    """Create a test tree structure similar to the one in the logs."""
    # Root node (depth 0)
    root = {
        'id': str(uuid.uuid4()),
        'question': "what is AI's impact on climate change?",
        'depth': 0,
        'needs_breakdown': True,
        'children': []
    }
    
    # Level 1 nodes - these should be siblings, not nested
    level1_node1 = {
        'id': str(uuid.uuid4()),
        'question': "What are the direct emissions from the use of AI systems?",
        'depth': 1,
        'needs_breakdown': True,
        'children': [],
        'parent_question': root['question']
    }
    
    level1_node2 = {
        'id': str(uuid.uuid4()),
        'question': "What are the indirect impacts of AI on energy consumption and greenhouse gas emissions?",
        'depth': 1,
        'needs_breakdown': True,
        'children': [],
        'parent_question': root['question']
    }
    
    level1_node3 = {
        'id': str(uuid.uuid4()),
        'question': "How can AI be used to help mitigate climate change?",
        'depth': 1,
        'needs_breakdown': True,
        'children': [],
        'parent_question': root['question']
    }
    
    # Level 2 nodes for first level 1 node
    level2_node1_1 = {
        'id': str(uuid.uuid4()),
        'question': "What are the carbon dioxide emissions from the operation of AI systems?",
        'depth': 2,
        'needs_breakdown': False,
        'answer': "Sample answer about carbon dioxide emissions from AI systems.",
        'parent_question': level1_node1['question']
    }
    
    level2_node1_2 = {
        'id': str(uuid.uuid4()),
        'question': "What are the energy consumption and carbon footprint of training large AI models?",
        'depth': 2,
        'needs_breakdown': False,
        'answer': "Sample answer about energy consumption of training large AI models.",
        'parent_question': level1_node1['question']
    }
    
    level2_node1_3 = {
        'id': str(uuid.uuid4()),
        'question': "What are the indirect emissions from the manufacturing and infrastructure supporting AI systems?",
        'depth': 2,
        'needs_breakdown': False,
        'answer': "Sample answer about indirect emissions from AI infrastructure.",
        'parent_question': level1_node1['question']
    }
    
    # Level 2 nodes for second level 1 node
    level2_node2_1 = {
        'id': str(uuid.uuid4()),
        'question': "How does AI-enabled automation and optimization impact energy consumption?",
        'depth': 2,
        'needs_breakdown': False,
        'answer': "Sample answer about AI-enabled automation and energy consumption.",
        'parent_question': level1_node2['question']
    }
    
    level2_node2_2 = {
        'id': str(uuid.uuid4()),
        'question': "How does the growing demand for AI computing power affect overall energy usage and emissions?",
        'depth': 2,
        'needs_breakdown': False,
        'answer': "Sample answer about growing demand for AI computing power.",
        'parent_question': level1_node2['question']
    }
    
    level2_node2_3 = {
        'id': str(uuid.uuid4()),
        'question': "What are the potential ways AI can be leveraged to reduce energy consumption and greenhouse gas emissions?",
        'depth': 2,
        'needs_breakdown': False,
        'answer': "Sample answer about AI reducing energy consumption.",
        'parent_question': level1_node2['question']
    }
    
    # Level 2 nodes for third level 1 node
    level2_node3_1 = {
        'id': str(uuid.uuid4()),
        'question': "What are the specific ways AI can help optimize renewable energy systems?",
        'depth': 2,
        'needs_breakdown': False,
        'answer': "Sample answer about AI optimizing renewable energy systems.",
        'parent_question': level1_node3['question']
    }
    
    level2_node3_2 = {
        'id': str(uuid.uuid4()),
        'question': "How can AI enhance environmental monitoring and data collection to support climate change mitigation efforts?",
        'depth': 2,
        'needs_breakdown': False,
        'answer': "Sample answer about AI enhancing environmental monitoring.",
        'parent_question': level1_node3['question']
    }
    
    level2_node3_3 = {
        'id': str(uuid.uuid4()),
        'question': "What are the potential risks or challenges in leveraging AI for climate change mitigation that need to be considered?",
        'depth': 2,
        'needs_breakdown': False,
        'answer': "Sample answer about risks in leveraging AI for climate change mitigation.",
        'parent_question': level1_node3['question']
    }
    
    # Add level 2 nodes to their respective level 1 parents
    level1_node1['children'] = [level2_node1_1, level2_node1_2, level2_node1_3]
    level1_node2['children'] = [level2_node2_1, level2_node2_2, level2_node2_3]
    level1_node3['children'] = [level2_node3_1, level2_node3_2, level2_node3_3]
    
    # Add level 1 nodes to root
    root['children'] = [level1_node1, level1_node2, level1_node3]
    
    return root

def main():
    """Generate and save test tree visualization."""
    # Create output directory
    os.makedirs('output', exist_ok=True)
    
    # Create test tree
    test_tree = create_test_tree()
    
    # Generate visualization
    visualization = generate_tree_visualization(test_tree)
    
    # Save visualization
    with open('output/test_tree.html', 'w') as f:
        f.write(visualization)
    
    # Save tree data for reference
    with open('output/test_tree_data.json', 'w') as f:
        json.dump(test_tree, f, indent=2)
    
    print("Test tree visualization saved to output/test_tree.html")
    print("Test tree data saved to output/test_tree_data.json")
    print("Open the HTML file in a browser to verify the visualization.")

if __name__ == '__main__':
    main() 