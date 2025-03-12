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

def create_basic_tree():
    """Create a basic tree structure for testing."""
    root = {
        'id': str(uuid.uuid4()),
        'question': 'What is a basic question?',
        'depth': 0,
        'needs_breakdown': True,
        'children': [
            {
                'id': str(uuid.uuid4()),
                'question': 'Child question 1?',
                'depth': 1,
                'needs_breakdown': False,
                'answer': 'Answer to child question 1',
                'sources': [{'title': 'Source 1', 'url': 'https://example.com/1'}]
            },
            {
                'id': str(uuid.uuid4()),
                'question': 'Child question 2?',
                'depth': 1,
                'needs_breakdown': False,
                'answer': 'Answer to child question 2',
                'sources': [{'title': 'Source 2', 'url': 'https://example.com/2'}]
            }
        ]
    }
    return root

def create_deep_tree():
    """Create a deep tree structure for testing."""
    root = {
        'id': str(uuid.uuid4()),
        'question': 'Level 0 Question?',
        'depth': 0,
        'needs_breakdown': True,
        'children': []
    }
    
    # Level 1
    level1 = {
        'id': str(uuid.uuid4()),
        'question': 'Level 1 Question?',
        'depth': 1,
        'needs_breakdown': True,
        'children': [],
        'parent_question': root['question']
    }
    
    # Level 2
    level2 = {
        'id': str(uuid.uuid4()),
        'question': 'Level 2 Question?',
        'depth': 2,
        'needs_breakdown': True,
        'children': [],
        'parent_question': level1['question']
    }
    
    # Level 3
    level3 = {
        'id': str(uuid.uuid4()),
        'question': 'Level 3 Question?',
        'depth': 3,
        'needs_breakdown': False,
        'answer': 'This is a level 3 answer.',
        'sources': [{'title': 'Deep Source', 'url': 'https://example.com/deep'}],
        'parent_question': level2['question']
    }
    
    # Build the tree
    level2['children'] = [level3]
    level1['children'] = [level2]
    root['children'] = [level1]
    
    return root

def create_edge_cases_tree():
    """Create a tree with edge cases for testing."""
    root = {
        'id': str(uuid.uuid4()),
        'question': 'Edge Cases Test?',
        'depth': 0,
        'needs_breakdown': True,
        'children': []
    }
    
    # Node without children
    node_no_children = {
        'id': str(uuid.uuid4()),
        'question': 'Node without children?',
        'depth': 1,
        'needs_breakdown': False,
        'answer': 'This node has no children.',
        'sources': [{'title': 'Source', 'url': 'https://example.com/source'}],
        'parent_question': root['question']
    }
    
    # Node without answer
    node_no_answer = {
        'id': str(uuid.uuid4()),
        'question': 'Node without answer?',
        'depth': 1,
        'needs_breakdown': False,
        'sources': [{'title': 'Source', 'url': 'https://example.com/source'}],
        'parent_question': root['question']
    }
    
    # Node without sources
    node_no_sources = {
        'id': str(uuid.uuid4()),
        'question': 'Node without sources?',
        'depth': 1,
        'needs_breakdown': False,
        'answer': 'This node has no sources.',
        'parent_question': root['question']
    }
    
    # Node with HTML content
    node_with_html = {
        'id': str(uuid.uuid4()),
        'question': 'Node with HTML content?',
        'depth': 1,
        'needs_breakdown': False,
        'answer': '<h1>HTML Title</h1><p>This is a <strong>paragraph</strong> with <em>HTML</em> content.</p>',
        'sources': [{'title': 'HTML Source', 'url': 'https://example.com/html'}],
        'parent_question': root['question']
    }
    
    # Node with very long question
    node_long_question = {
        'id': str(uuid.uuid4()),
        'question': 'This is a very long question that should test how the visualization handles long text content and whether it wraps properly or causes layout issues when the text is extremely long and verbose and contains many words that might cause the layout to break if not handled correctly?',
        'depth': 1,
        'needs_breakdown': False,
        'answer': 'Answer to long question.',
        'sources': [{'title': 'Long Source', 'url': 'https://example.com/long'}],
        'parent_question': root['question']
    }
    
    # Add all nodes to root
    root['children'] = [
        node_no_children,
        node_no_answer,
        node_no_sources,
        node_with_html,
        node_long_question
    ]
    
    return root

def main():
    """Generate and save test tree visualizations."""
    # Create output directory
    os.makedirs('output', exist_ok=True)
    
    # Test 1: Sample Tree (Complex AI and Climate Change)
    sample_tree = create_sample_tree()
    sample_visualization = generate_tree_visualization(sample_tree)
    with open('output/sample_tree.html', 'w') as f:
        f.write(sample_visualization)
    with open('output/sample_tree_data.json', 'w') as f:
        json.dump(sample_tree, f, indent=2)
    print("Sample tree visualization saved to output/sample_tree.html")
    
    # Test 2: Basic Tree
    basic_tree = create_basic_tree()
    basic_visualization = generate_tree_visualization(basic_tree)
    with open('output/basic_tree.html', 'w') as f:
        f.write(basic_visualization)
    with open('output/basic_tree_data.json', 'w') as f:
        json.dump(basic_tree, f, indent=2)
    print("Basic tree visualization saved to output/basic_tree.html")
    
    # Test 3: Deep Tree
    deep_tree = create_deep_tree()
    deep_visualization = generate_tree_visualization(deep_tree)
    with open('output/deep_tree.html', 'w') as f:
        f.write(deep_visualization)
    with open('output/deep_tree_data.json', 'w') as f:
        json.dump(deep_tree, f, indent=2)
    print("Deep tree visualization saved to output/deep_tree.html")
    
    # Test 4: Edge Cases
    edge_tree = create_edge_cases_tree()
    edge_visualization = generate_tree_visualization(edge_tree)
    with open('output/edge_cases_tree.html', 'w') as f:
        f.write(edge_visualization)
    with open('output/edge_cases_tree_data.json', 'w') as f:
        json.dump(edge_tree, f, indent=2)
    print("Edge cases tree visualization saved to output/edge_cases_tree.html")
    
    print("\nAll test visualizations have been generated. Open the HTML files in a browser to view them.")

if __name__ == '__main__':
    main() 