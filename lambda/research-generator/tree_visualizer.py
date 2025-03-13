"""
Functions for visualizing the question tree.
"""

def validate_tree_structure(node, parent_depth=None, path=""):
    """
    Validate the tree structure to ensure it's sound for visualization.
    
    Args:
        node: The node to validate
        parent_depth: The depth of the parent node
        path: The path to this node (for error reporting)
    
    Returns:
        tuple: (is_valid, issues)
    """
    issues = []
    
    # Check if node has required properties
    if 'id' not in node:
        issues.append(f"Node at {path} is missing 'id' property")
    
    if 'question' not in node:
        issues.append(f"Node at {path} is missing 'question' property")
    
    if 'depth' not in node:
        issues.append(f"Node at {path} is missing 'depth' property")
        # We can't validate depth consistency without the depth property
        return False, issues
    
    # Check depth consistency
    depth = node['depth']
    if parent_depth is not None and depth != parent_depth + 1:
        issues.append(f"Node at {path} has inconsistent depth: {depth} (parent depth: {parent_depth})")
    
    # Check children
    if node.get('needs_breakdown', False) and node.get('children'):
        for i, child in enumerate(node['children']):
            child_path = f"{path}/{i}"
            child_valid, child_issues = validate_tree_structure(child, depth, child_path)
            issues.extend(child_issues)
    
    return len(issues) == 0, issues

def generate_tree_visualization(question_tree):
    """
    Generate an interactive HTML visualization of the question tree
    with collapsible nodes and detailed view on click
    """
    # Validate tree structure
    is_valid, issues = validate_tree_structure(question_tree)
    if not is_valid:
        print("WARNING: Tree structure validation failed with the following issues:")
        for issue in issues:
            print(f"  - {issue}")
        print("Attempting to visualize anyway...")
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Research Question Tree</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 20px;
                line-height: 1.5;
                color: #333;
            }
            .tree-container {
                max-width: 1000px;
                margin: 20px auto;
                position: relative;
            }
            .node {
                margin: 10px 0;
                border-radius: 4px;
                overflow: hidden;
                position: relative;
            }
            .question-node {
                background-color: #f5f8ff;
                border-left: 3px solid #4a6fa5;
            }
            /* Style nodes differently based on their logical depth */
            .question-node[data-depth="0"] {
                border-left-color: #4a6fa5;
                background-color: #f0f5ff;
            }
            .question-node[data-depth="1"] {
                border-left-color: #5c7cfa;
                background-color: #f5f8ff;
            }
            .question-node[data-depth="2"] {
                border-left-color: #748ffc;
                background-color: #f8faff;
            }
            .answer-node {
                background-color: #f5fff8;
                border-left: 3px solid #4caf50;
                margin-left: 20px;
                padding: 10px;
                display: none; /* Hidden by default */
            }
            .node-header {
                padding: 10px 15px;
                cursor: pointer;
                display: flex;
                align-items: center;
            }
            .node-title {
                font-weight: 500;
                flex-grow: 1;
            }
            .depth-indicator {
                color: #666;
                font-size: 0.8em;
                margin-right: 10px;
                background-color: #eee;
                padding: 2px 6px;
                border-radius: 10px;
            }
            /* Style depth indicators based on logical depth */
            .question-node[data-depth="0"] .depth-indicator {
                background-color: #e7f0ff;
                color: #4a6fa5;
            }
            .question-node[data-depth="1"] .depth-indicator {
                background-color: #edf2ff;
                color: #5c7cfa;
            }
            .question-node[data-depth="2"] .depth-indicator {
                background-color: #f3f6ff;
                color: #748ffc;
            }
            .toggle-icon {
                font-size: 16px;
                width: 20px;
                text-align: center;
            }
            /* Base children container styling */
            .children {
                position: relative;
                display: none; /* Hidden by default */
                border-left: 1px dashed #ccc;
            }
            /* Show children when expanded */
            .expanded > .children, 
            .expanded > .answer-node {
                display: block;
            }
            h1 {
                color: #4a6fa5;
                font-size: 1.5rem;
                margin-bottom: 10px;
            }
            p {
                margin-top: 0;
                color: #666;
            }
            button {
                background-color: #4a6fa5;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 0.8em;
                cursor: pointer;
                margin: 5px 0;
            }
            button:hover {
                background-color: #3b5998;
            }
            .sources {
                margin-top: 15px;
                padding-top: 10px;
                border-top: 1px solid #eee;
                font-size: 0.8em;
            }
            .sources h4 {
                margin: 0 0 5px 0;
                color: #666;
                font-size: 0.9em;
            }
            .sources ul {
                margin: 0;
                padding-left: 20px;
                color: #777;
            }
            .sources a {
                color: #4a6fa5;
                text-decoration: none;
            }
            .sources a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <h1>Research Question Tree</h1>
        <p>Click on any question to expand/collapse.</p>
        
        <div class="tree-container">
    """
    
    # Add the tree structure
    html += render_interactive_node_html(question_tree)
    
    # Add the closing tags and script
    html += """
        </div>
        
        <script>
            // Toggle node expansion
            function toggleNode(nodeId) {
                const node = document.getElementById(nodeId);
                node.classList.toggle('expanded');
                
                // Update toggle icon
                const icon = node.querySelector('.toggle-icon');
                if (node.classList.contains('expanded')) {
                    icon.textContent = '−';
                } else {
                    icon.textContent = '+';
                }
            }
            
            // Expand the root node on load
            document.addEventListener('DOMContentLoaded', function() {
                const rootNode = document.querySelector('.tree-container > .question-node');
                if (rootNode) {
                    rootNode.classList.add('expanded');
                    const icon = rootNode.querySelector('.toggle-icon');
                    if (icon) icon.textContent = '−';
                }
            });
        </script>
    </body>
    </html>
    """
    
    return html

def render_interactive_node_html(node, path="", parent_depth=None):
    """
    Render a single node of the question tree as interactive HTML
    
    Args:
        node: The node to render
        path: The path to this node (for breadcrumb display)
        parent_depth: The depth of the parent node (for consistent level numbering)
    """
    # Get the depth from the node
    depth = node['depth']
    node_id = node['id']
    
    # Calculate indentation based on depth - simple and direct approach
    indent_style = f"margin-left: {depth * 20}px;"
    
    # Create the node HTML with direct styling for indentation
    html = f"""
    <div class="node question-node" id="{node_id}" data-depth="{depth}" style="{indent_style}">
        <div class="node-header" onclick="toggleNode('{node_id}')">
            <span class="depth-indicator">Level {depth}</span>
            <span class="node-title">{node['question']}</span>
            <span class="toggle-icon">+</span>
        </div>
    """
    
    if node.get('needs_breakdown', False) and node.get('children'):
        # Add a small left margin to the children container for the connecting line
        html += '<div class="children" style="margin-left: 10px;">'
        
        # Process each child node
        for child in node['children']:
            child_html = render_interactive_node_html(child, path)
            html += child_html
            
        html += '</div>'
    else:
        html += f"""
        <div class="answer-node">
            <div>{node.get('answer', 'No answer available')}</div>
        """
        
        # Add sources if available
        if node.get('sources'):
            html += """
            <div class="sources">
                <h4>Sources:</h4>
                <ul>
            """
            for source in node.get('sources', []):
                title = source.get('title', 'Untitled Source')
                url = source.get('url', '#')
                html += f'<li><a href="{url}" target="_blank">{title}</a></li>'
            
            html += """
                </ul>
            </div>
            """
            
        html += """
        </div>
        """
    
    html += '</div>'
    return html 