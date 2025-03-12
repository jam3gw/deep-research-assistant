"""
Functions for visualizing the question tree.
"""

def generate_tree_visualization(question_tree):
    """
    Generate an interactive HTML visualization of the question tree
    with collapsible nodes and detailed view on click
    """
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
            }
            .node {
                margin: 10px 0;
                border-radius: 4px;
                overflow: hidden;
            }
            .question-node {
                background-color: #f5f8ff;
                border-left: 3px solid #4a6fa5;
            }
            /* Style nodes differently based on their depth */
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
            /* Style depth indicators based on level */
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
            .children {
                margin-left: 25px;
                border-left: 1px dashed #ccc;
                padding-left: 15px;
                display: none; /* Hidden by default */
            }
            .expanded > .children, 
            .expanded > .answer-node {
                display: block; /* Show when expanded */
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
    # Get the original depth from the node
    original_depth = node['depth']
    
    # Calculate the display depth (for consistent level numbering)
    # If this is a root node (no parent_depth), use the original depth
    # Otherwise, use parent_depth + 1 to ensure consistent hierarchy
    display_depth = original_depth
    
    # Only use parent_depth for visual nesting, not for the actual level indicator
    visual_depth = parent_depth + 1 if parent_depth is not None else 0
    
    node_id = node['id']
    
    html = f"""
    <div class="node question-node" id="{node_id}" data-depth="{display_depth}">
        <div class="node-header" onclick="toggleNode('{node_id}')">
            <span class="depth-indicator">Level {display_depth}</span>
            <span class="node-title">{node['question']}</span>
            <span class="toggle-icon">+</span>
        </div>
    """
    
    if node.get('needs_breakdown', False) and node.get('children'):
        html += '<div class="children">'
        for child in node['children']:
            # Pass the current visual_depth as the parent_depth for the child
            html += render_interactive_node_html(child, path, visual_depth)
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