#!/usr/bin/env python3
"""
Test script for the tree visualization component.
This allows you to test the tree visualization with a sample question tree.
"""

import os
import json
import uuid
from tree_visualizer import generate_tree_visualization

def create_sample_tree():
    """Create a sample question tree for testing."""
    # Root node (depth 0)
    root = {
        'id': str(uuid.uuid4()),
        'question': 'What is AI\'s impact on climate change?',
        'depth': 0,
        'needs_breakdown': True,
        'children': []
    }
    
    # Level 1 nodes
    level1_node1 = {
        'id': str(uuid.uuid4()),
        'question': 'How is AI contributing to climate change beyond its emissions?',
        'depth': 1,
        'needs_breakdown': True,
        'children': [],
        'parent_question': root['question']
    }
    
    level1_node2 = {
        'id': str(uuid.uuid4()),
        'question': 'How is AI being used to solve environmental problems?',
        'depth': 1,
        'needs_breakdown': True,
        'children': [],
        'parent_question': root['question']
    }
    
    # Level 2 nodes for first level 1 node
    level2_node1 = {
        'id': str(uuid.uuid4()),
        'question': 'How is the increasing efficiency of AI in solving environmental problems contributing to climate change?',
        'depth': 2,
        'needs_breakdown': False,
        'answer': 'AI systems are becoming more efficient at solving environmental problems, which can help reduce emissions in various sectors.',
        'sources': [
            {'title': 'AI and Climate Change', 'url': 'https://example.com/ai-climate'},
            {'title': 'Environmental Applications of AI', 'url': 'https://example.com/ai-environment'}
        ],
        'parent_question': level1_node1['question']
    }
    
    level2_node2 = {
        'id': str(uuid.uuid4()),
        'question': 'What other ways, beyond direct emissions, is AI contributing to climate change?',
        'depth': 2,
        'needs_breakdown': False,
        'answer': 'AI can contribute to climate change through increased energy consumption, resource extraction for hardware, and enabling more efficient fossil fuel extraction.',
        'sources': [
            {'title': 'Hidden Costs of AI', 'url': 'https://example.com/ai-hidden-costs'},
            {'title': 'AI Energy Usage', 'url': 'https://example.com/ai-energy'}
        ],
        'parent_question': level1_node1['question']
    }
    
    level2_node3 = {
        'id': str(uuid.uuid4()),
        'question': 'How do the indirect impacts of AI on climate change compare to its direct emissions?',
        'depth': 2,
        'needs_breakdown': False,
        'answer': 'The indirect impacts of AI on climate change, such as enabling more efficient resource extraction or changing consumption patterns, can be more significant than its direct energy usage.',
        'sources': [
            {'title': 'AI Indirect Effects', 'url': 'https://example.com/ai-indirect'},
            {'title': 'Comparing AI Impacts', 'url': 'https://example.com/ai-impacts-comparison'}
        ],
        'parent_question': level1_node1['question']
    }
    
    # Level 2 nodes for second level 1 node
    level2_node4 = {
        'id': str(uuid.uuid4()),
        'question': 'How can AI enhance energy efficiency and reduce energy usage?',
        'depth': 2,
        'needs_breakdown': False,
        'answer': 'AI can optimize energy systems, improve building efficiency, and enable smart grid technologies to reduce overall energy consumption.',
        'sources': [
            {'title': 'AI for Energy Efficiency', 'url': 'https://example.com/ai-energy-efficiency'},
            {'title': 'Smart Grid AI', 'url': 'https://example.com/smart-grid-ai'}
        ],
        'parent_question': level1_node2['question']
    }
    
    level2_node5 = {
        'id': str(uuid.uuid4()),
        'question': 'How can AI assist in environmental monitoring?',
        'depth': 2,
        'needs_breakdown': False,
        'answer': 'AI can process satellite imagery, sensor data, and other environmental information to monitor deforestation, pollution, and climate change impacts.',
        'sources': [
            {'title': 'AI Environmental Monitoring', 'url': 'https://example.com/ai-monitoring'},
            {'title': 'Satellite AI', 'url': 'https://example.com/satellite-ai'}
        ],
        'parent_question': level1_node2['question']
    }
    
    # Add level 2 nodes to their respective level 1 parents
    level1_node1['children'] = [level2_node1, level2_node2, level2_node3]
    level1_node2['children'] = [level2_node4, level2_node5]
    
    # Add level 1 nodes to root
    root['children'] = [level1_node1, level1_node2]
    
    # Add a level 1 node with no children
    level1_node3 = {
        'id': str(uuid.uuid4()),
        'question': 'What are the potential positive and negative impacts of AI on climate change?',
        'depth': 1,
        'needs_breakdown': False,
        'answer': 'AI has both positive impacts (enabling clean energy, optimizing resource use) and negative impacts (energy consumption, enabling fossil fuel extraction) on climate change.',
        'sources': [
            {'title': 'Dual Impact of AI', 'url': 'https://example.com/ai-dual-impact'},
            {'title': 'AI Climate Balance', 'url': 'https://example.com/ai-climate-balance'}
        ],
        'parent_question': root['question']
    }
    root['children'].append(level1_node3)
    
    return root

def main():
    """Generate and save a test tree visualization."""
    # Create sample tree
    question_tree = create_sample_tree()
    
    # Generate tree visualization
    print("Generating tree visualization...")
    tree_visualization = generate_tree_visualization(question_tree)
    
    # Save tree visualization
    os.makedirs('output', exist_ok=True)
    with open('output/test_tree.html', 'w') as f:
        f.write(tree_visualization)
    
    # Save tree data for reference
    with open('output/test_tree_data.json', 'w') as f:
        json.dump(question_tree, f, indent=2)
    
    print("Tree visualization saved to output/test_tree.html")
    print("Tree data saved to output/test_tree_data.json")

if __name__ == '__main__':
    main() 