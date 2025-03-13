#!/usr/bin/env python3
"""
Consolidated test script for the tree visualization component.
This allows you to test the tree visualization with various sample question trees.
"""

import os
import json
import uuid
import argparse
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
        'question': 'What are the direct emissions from the use of AI systems?',
        'depth': 1,
        'needs_breakdown': True,
        'children': [],
        'parent_question': root['question']
    }
    
    level1_node2 = {
        'id': str(uuid.uuid4()),
        'question': 'How can AI be used to help mitigate climate change?',
        'depth': 1,
        'needs_breakdown': True,
        'children': [],
        'parent_question': root['question']
    }
    
    # Level 2 nodes for first level 1 node
    level2_node1_1 = {
        'id': str(uuid.uuid4()),
        'question': 'What are the carbon dioxide emissions from the operation of AI systems?',
        'depth': 2,
        'needs_breakdown': False,
        'answer': 'The operation of AI systems, particularly large language models and deep learning systems, can generate significant carbon dioxide emissions. Training a single large AI model can emit as much carbon as five cars over their lifetimes. These emissions come primarily from electricity consumption in data centers, which often rely on fossil fuels. The carbon footprint varies greatly depending on the location of data centers and their energy sources.',
        'parent_question': level1_node1['question']
    }
    
    level2_node1_2 = {
        'id': str(uuid.uuid4()),
        'question': 'What are the energy consumption patterns of AI inference versus training?',
        'depth': 2,
        'needs_breakdown': False,
        'answer': 'AI training typically requires more energy upfront but happens less frequently, while inference (using the trained model) consumes less energy per instance but occurs much more frequently. As AI systems become more widely deployed, the cumulative energy consumption from inference may eventually exceed that of training. Efficient model design and hardware optimization are crucial for reducing both training and inference energy consumption.',
        'parent_question': level1_node1['question']
    }
    
    # Level 2 nodes for second level 1 node
    level2_node2_1 = {
        'id': str(uuid.uuid4()),
        'question': 'How can AI optimize renewable energy systems?',
        'depth': 2,
        'needs_breakdown': False,
        'answer': 'AI can optimize renewable energy systems through predictive maintenance, forecasting energy production based on weather patterns, balancing supply and demand in smart grids, and optimizing energy storage. Machine learning algorithms can predict solar and wind power generation with increasing accuracy, helping grid operators integrate more renewable energy. AI can also optimize the placement of renewable energy infrastructure for maximum efficiency.',
        'parent_question': level1_node2['question']
    }
    
    level2_node2_2 = {
        'id': str(uuid.uuid4()),
        'question': 'What role can AI play in carbon capture and sequestration?',
        'depth': 2,
        'needs_breakdown': False,
        'answer': 'AI can enhance carbon capture and sequestration by optimizing capture processes, identifying ideal geological storage locations, monitoring carbon leakage, and accelerating the development of new carbon capture materials. Machine learning models can analyze vast datasets to identify patterns and optimize complex carbon capture chemical processes. AI can also help monitor and verify carbon offsets and sequestration projects to ensure their effectiveness.',
        'parent_question': level1_node2['question']
    }
    
    # Add level 2 nodes to their respective level 1 parents
    level1_node1['children'] = [level2_node1_1, level2_node1_2]
    level1_node2['children'] = [level2_node2_1, level2_node2_2]
    
    # Add level 1 nodes to root
    root['children'] = [level1_node1, level1_node2]
    
    return root

def create_complex_tree():
    """Create a more complex test tree structure with multiple levels and branches."""
    # Root node (depth 0)
    root = {
        'id': str(uuid.uuid4()),
        'question': "What are the key differences between supervised and unsupervised learning?",
        'depth': 0,
        'needs_breakdown': True,
        'children': []
    }
    
    # Level 1 nodes - these should be siblings, not nested
    level1_node1 = {
        'id': str(uuid.uuid4()),
        'question': "How does supervised learning work?",
        'depth': 1,
        'needs_breakdown': True,
        'children': [],
        'parent_question': root['question']
    }
    
    level1_node2 = {
        'id': str(uuid.uuid4()),
        'question': "How does unsupervised learning work?",
        'depth': 1,
        'needs_breakdown': True,
        'children': [],
        'parent_question': root['question']
    }
    
    level1_node3 = {
        'id': str(uuid.uuid4()),
        'question': "What are the applications of supervised vs. unsupervised learning?",
        'depth': 1,
        'needs_breakdown': True,
        'children': [],
        'parent_question': root['question']
    }
    
    # Level 2 nodes for first level 1 node
    level2_node1_1 = {
        'id': str(uuid.uuid4()),
        'question': "What types of problems can supervised learning solve?",
        'depth': 2,
        'needs_breakdown': False,
        'answer': "Supervised learning can solve classification problems (assigning categories) and regression problems (predicting continuous values). It's effective when you have labeled data and a clear target variable to predict.",
        'parent_question': level1_node1['question']
    }
    
    level2_node1_2 = {
        'id': str(uuid.uuid4()),
        'question': "What are common supervised learning algorithms?",
        'depth': 2,
        'needs_breakdown': False,
        'answer': "Common supervised learning algorithms include Linear Regression, Logistic Regression, Support Vector Machines (SVM), Decision Trees, Random Forests, Gradient Boosting, and Neural Networks. Each has different strengths and is suited to different types of problems.",
        'parent_question': level1_node1['question']
    }
    
    # Level 2 nodes for second level 1 node
    level2_node2_1 = {
        'id': str(uuid.uuid4()),
        'question': "What types of problems can unsupervised learning solve?",
        'depth': 2,
        'needs_breakdown': False,
        'answer': "Unsupervised learning can solve clustering problems (grouping similar data points), dimensionality reduction (simplifying data while preserving information), and anomaly detection (identifying outliers). It's useful when you don't have labeled data or when you're exploring data to discover patterns.",
        'parent_question': level1_node2['question']
    }
    
    level2_node2_2 = {
        'id': str(uuid.uuid4()),
        'question': "What are common unsupervised learning algorithms?",
        'depth': 2,
        'needs_breakdown': False,
        'answer': "Common unsupervised learning algorithms include K-Means Clustering, Hierarchical Clustering, DBSCAN, Principal Component Analysis (PCA), t-SNE, Autoencoders, and Generative Adversarial Networks (GANs). These algorithms help identify patterns without predefined labels.",
        'parent_question': level1_node2['question']
    }
    
    # Level 2 nodes for third level 1 node
    level2_node3_1 = {
        'id': str(uuid.uuid4()),
        'question': "Where is supervised learning commonly applied?",
        'depth': 2,
        'needs_breakdown': False,
        'answer': "Supervised learning is commonly applied in email spam detection, sentiment analysis, image recognition, medical diagnosis, credit scoring, recommendation systems, and predictive maintenance. Any problem where historical labeled data exists is a candidate for supervised learning.",
        'parent_question': level1_node3['question']
    }
    
    level2_node3_2 = {
        'id': str(uuid.uuid4()),
        'question': "Where is unsupervised learning commonly applied?",
        'depth': 2,
        'needs_breakdown': False,
        'answer': "Unsupervised learning is commonly applied in customer segmentation, topic modeling in text, anomaly detection in security systems, feature learning, recommendation systems, and exploratory data analysis. It's valuable when you want to discover hidden patterns or when labeled data is unavailable.",
        'parent_question': level1_node3['question']
    }
    
    # Add level 2 nodes to their respective level 1 parents
    level1_node1['children'] = [level2_node1_1, level2_node1_2]
    level1_node2['children'] = [level2_node2_1, level2_node2_2]
    level1_node3['children'] = [level2_node3_1, level2_node3_2]
    
    # Add level 1 nodes to root
    root['children'] = [level1_node1, level1_node2, level1_node3]
    
    return root

def create_deep_tree():
    """Create a deep tree with multiple levels for testing depth handling."""
    # Root node (depth 0)
    root = {
        'id': str(uuid.uuid4()),
        'question': 'How do quantum computers work?',
        'depth': 0,
        'needs_breakdown': True,
        'children': []
    }
    
    # Level 1
    level1_node = {
        'id': str(uuid.uuid4()),
        'question': 'What are the fundamental principles of quantum computing?',
        'depth': 1,
        'needs_breakdown': True,
        'children': [],
        'parent_question': root['question']
    }
    
    # Level 2
    level2_node = {
        'id': str(uuid.uuid4()),
        'question': 'How do qubits differ from classical bits?',
        'depth': 2,
        'needs_breakdown': True,
        'children': [],
        'parent_question': level1_node['question']
    }
    
    # Level 3
    level3_node = {
        'id': str(uuid.uuid4()),
        'question': 'What is quantum superposition?',
        'depth': 3,
        'needs_breakdown': True,
        'children': [],
        'parent_question': level2_node['question']
    }
    
    # Level 4
    level4_node = {
        'id': str(uuid.uuid4()),
        'question': 'How is quantum superposition measured?',
        'depth': 4,
        'needs_breakdown': False,
        'answer': 'Quantum superposition is measured through a process called quantum measurement or wave function collapse. When a measurement is performed on a qubit in superposition, it collapses to either 0 or 1 with probabilities determined by the quantum state. This measurement process is probabilistic rather than deterministic, which is a fundamental aspect of quantum mechanics.',
        'parent_question': level3_node['question']
    }
    
    # Build the tree from bottom up
    level3_node['children'] = [level4_node]
    level2_node['children'] = [level3_node]
    level1_node['children'] = [level2_node]
    root['children'] = [level1_node]
    
    return root

def main():
    """Generate and save test tree visualizations."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate test tree visualizations')
    parser.add_argument('--type', choices=['sample', 'complex', 'deep', 'all'], default='all',
                        help='Type of test tree to generate (default: all)')
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs('output', exist_ok=True)
    
    # Generate visualizations based on the specified type
    if args.type in ['sample', 'all']:
        sample_tree = create_sample_tree()
        sample_visualization = generate_tree_visualization(sample_tree)
        with open('output/sample_tree.html', 'w') as f:
            f.write(sample_visualization)
        with open('output/sample_tree.json', 'w') as f:
            json.dump(sample_tree, f, indent=2)
        print("Sample tree visualization saved to output/sample_tree.html")
    
    if args.type in ['complex', 'all']:
        complex_tree = create_complex_tree()
        complex_visualization = generate_tree_visualization(complex_tree)
        with open('output/complex_tree.html', 'w') as f:
            f.write(complex_visualization)
        with open('output/complex_tree.json', 'w') as f:
            json.dump(complex_tree, f, indent=2)
        print("Complex tree visualization saved to output/complex_tree.html")
    
    if args.type in ['deep', 'all']:
        deep_tree = create_deep_tree()
        deep_visualization = generate_tree_visualization(deep_tree)
        with open('output/deep_tree.html', 'w') as f:
            f.write(deep_visualization)
        with open('output/deep_tree.json', 'w') as f:
            json.dump(deep_tree, f, indent=2)
        print("Deep tree visualization saved to output/deep_tree.html")
    
    print("Open the HTML files in a browser to verify the visualizations.")

if __name__ == '__main__':
    main() 