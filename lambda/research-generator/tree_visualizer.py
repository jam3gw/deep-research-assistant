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
                font-family: Arial, sans-serif;
                margin: 20px;
                line-height: 1.6;
            }
            .tree-container {
                margin: 20px 0;
            }
            .node {
                margin: 10px 0;
                border-radius: 5px;
                overflow: hidden;
            }
            .question-node {
                background-color: #e6f7ff;
                border-left: 4px solid #1890ff;
            }
            .max-depth-node {
                background-color: #fff7e6;
                border-left: 4px solid #fa8c16;
            }
            .vague-node {
                background-color: #f9f0ff;
                border-left: 4px solid #722ed1;
            }
            .answer-node {
                background-color: #f6ffed;
                border-left: 4px solid #52c41a;
                margin-left: 20px;
                padding: 10px;
                display: none; /* Hidden by default */
            }
            .node-header {
                padding: 10px;
                cursor: pointer;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .node-title {
                font-weight: bold;
                flex-grow: 1;
            }
            .depth-indicator {
                color: #888;
                font-size: 0.8em;
                margin-right: 10px;
                background-color: #f0f0f0;
                padding: 2px 6px;
                border-radius: 10px;
                display: inline-block;
            }
            .path-indicator {
                color: #888;
                font-size: 0.8em;
                margin-left: 10px;
                font-style: italic;
            }
            .toggle-icon {
                font-size: 18px;
                width: 20px;
                text-align: center;
            }
            .children {
                margin-left: 30px;
                border-left: 1px dashed #d9d9d9;
                padding-left: 20px;
                display: none; /* Hidden by default */
            }
            .expanded > .children, 
            .expanded > .answer-node {
                display: block; /* Show when expanded */
            }
            .node-content {
                padding: 0 10px 10px 10px;
            }
            .max-depth-badge {
                display: inline-block;
                background-color: #fa8c16;
                color: white;
                font-size: 0.8em;
                padding: 2px 8px;
                border-radius: 10px;
                margin-left: 10px;
            }
            .vague-badge {
                display: inline-block;
                background-color: #722ed1;
                color: white;
                font-size: 0.8em;
                padding: 2px 8px;
                border-radius: 10px;
                margin-left: 10px;
            }
            .detail-view {
                position: fixed;
                top: 0;
                right: 0;
                width: 40%;
                height: 100%;
                background: white;
                border-left: 1px solid #ccc;
                box-shadow: -2px 0 5px rgba(0,0,0,0.1);
                padding: 20px;
                overflow-y: auto;
                transform: translateX(100%);
                transition: transform 0.3s ease;
                z-index: 1000;
            }
            .detail-view.active {
                transform: translateX(0);
            }
            .detail-view-close {
                position: absolute;
                top: 10px;
                right: 10px;
                font-size: 24px;
                cursor: pointer;
                background: none;
                border: none;
            }
            .detail-view-title {
                margin-top: 0;
                padding-right: 30px;
            }
            .detail-view-content {
                margin-top: 20px;
            }
            .expand-all-btn, .collapse-all-btn {
                background-color: #1890ff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                cursor: pointer;
                margin-right: 10px;
                margin-bottom: 20px;
            }
            .collapse-all-btn {
                background-color: #52c41a;
            }
            .button-container {
                margin-bottom: 20px;
            }
            .note {
                background-color: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 15px;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <h1>Research Question Tree</h1>
        <p>Click on any question to expand/collapse. Click "View Details" to see the full answer.</p>
        
        <div class="button-container">
            <button class="expand-all-btn" onclick="expandAll()">Expand All</button>
            <button class="collapse-all-btn" onclick="collapseAll()">Collapse All</button>
        </div>
        
        <div class="tree-container">
    """
    
    # Add the tree structure
    html += render_interactive_node_html(question_tree)
    
    # Add the detail view panel
    html += """
        </div>
        
        <div class="detail-view" id="detailView">
            <button class="detail-view-close" onclick="closeDetailView()">&times;</button>
            <h2 class="detail-view-title" id="detailViewTitle">Question Details</h2>
            <div class="detail-view-content" id="detailViewContent"></div>
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
            
            // Show detail view
            function showDetails(nodeId, isQuestion) {
                const node = document.getElementById(nodeId);
                const detailView = document.getElementById('detailView');
                const detailViewTitle = document.getElementById('detailViewTitle');
                const detailViewContent = document.getElementById('detailViewContent');
                
                if (isQuestion) {
                    const questionText = node.querySelector('.node-title').textContent.split(':')[1].trim();
                    detailViewTitle.textContent = 'Question: ' + questionText;
                    
                    // Check if this node has children or an answer
                    const children = node.querySelector('.children');
                    const answer = node.querySelector('.answer-node');
                    
                    let content = '';
                    if (children && children.childElementCount > 0) {
                        content = '<h3>Sub-questions:</h3><ul>';
                        const subQuestions = children.querySelectorAll('.node-title');
                        subQuestions.forEach(sq => {
                            content += '<li>' + sq.textContent.split(':')[1].trim() + '</li>';
                        });
                        content += '</ul>';
                    } else if (answer) {
                        content = '<h3>Answer:</h3>' + answer.innerHTML;
                    } else {
                        content = '<p>No answer or sub-questions available.</p>';
                    }
                    
                    detailViewContent.innerHTML = content;
                } else {
                    // It's an answer node
                    const questionNode = node.closest('.question-node');
                    const questionText = questionNode.querySelector('.node-title').textContent.split(':')[1].trim();
                    detailViewTitle.textContent = 'Answer to: ' + questionText;
                    
                    // Get the answer content
                    detailViewContent.innerHTML = node.innerHTML;
                }
                
                detailView.classList.add('active');
            }
            
            // Close detail view
            function closeDetailView() {
                document.getElementById('detailView').classList.remove('active');
            }
            
            // Expand all nodes
            function expandAll() {
                document.querySelectorAll('.question-node').forEach(node => {
                    node.classList.add('expanded');
                    const icon = node.querySelector('.toggle-icon');
                    if (icon) icon.textContent = '−';
                });
            }
            
            // Collapse all nodes
            function collapseAll() {
                document.querySelectorAll('.question-node').forEach(node => {
                    // Don't collapse the root node
                    if (node.parentElement.classList.contains('tree-container')) {
                        node.classList.add('expanded');
                        const icon = node.querySelector('.toggle-icon');
                        if (icon) icon.textContent = '−';
                    } else {
                        node.classList.remove('expanded');
                        const icon = node.querySelector('.toggle-icon');
                        if (icon) icon.textContent = '+';
                    }
                });
            }
            
            // Validate tree structure on load
            document.addEventListener('DOMContentLoaded', function() {
                // Expand the root node
                const rootNode = document.querySelector('.tree-container > .question-node');
                if (rootNode) {
                    rootNode.classList.add('expanded');
                    const icon = rootNode.querySelector('.toggle-icon');
                    if (icon) icon.textContent = '−';
                }
                
                // Validate the tree structure
                validateTreeStructure();
            });
            
            // Function to validate and fix tree structure
            function validateTreeStructure() {
                // Get all nodes
                const allNodes = document.querySelectorAll('.question-node');
                
                allNodes.forEach(node => {
                    const nodeDepth = parseInt(node.getAttribute('data-depth'));
                    const parentNode = node.parentElement.closest('.question-node');
                    
                    // If this is not the root node and has a parent
                    if (parentNode) {
                        const parentDepth = parseInt(parentNode.getAttribute('data-depth'));
                        
                        // Check if the depth is correct (should be parent depth + 1)
                        if (nodeDepth !== parentDepth + 1) {
                            console.warn(`Node depth mismatch: Node ${node.id} has depth ${nodeDepth} but parent ${parentNode.id} has depth ${parentDepth}`);
                            
                            // Update the displayed depth
                            const depthIndicator = node.querySelector('.depth-indicator');
                            if (depthIndicator) {
                                depthIndicator.textContent = `Level ${parentDepth + 1}`;
                            }
                        }
                    }
                });
            }
        </script>
    </body>
    </html>
    """
    
    return html

def render_interactive_node_html(node, path=""):
    """
    Render a single node of the question tree as interactive HTML
    """
    depth = node['depth']
    node_id = node['id']
    
    # Add a special class if this node reached max depth or is vague
    max_depth_class = " max-depth-node" if node.get('max_depth_reached', False) else ""
    vague_class = " vague-node" if node.get('is_vague', False) else ""
    
    # Create the path for this node
    current_path = path + (f" > {node['question'][:20]}..." if path else "")
    
    html = f"""
    <div class="node question-node{max_depth_class}{vague_class}" id="{node_id}" data-depth="{depth}">
        <div class="node-header" onclick="toggleNode('{node_id}')">
            <span class="depth-indicator">Level {depth}</span>
            <span class="node-title">Question: {node['question']}</span>
            <span class="toggle-icon">+</span>
        </div>
        <div class="node-content">
            <button onclick="showDetails('{node_id}', true); event.stopPropagation();">View Details</button>
            {f'<span class="max-depth-badge">Max Depth</span>' if node.get('max_depth_reached', False) else ''}
            {f'<span class="vague-badge">Vague Question</span>' if node.get('is_vague', False) else ''}
            <div class="path-indicator">{current_path}</div>
        </div>
    """
    
    if node.get('needs_breakdown', False) and node.get('children'):
        html += '<div class="children">'
        for child in node['children']:
            # Ensure child depth is correctly set relative to parent
            if child['depth'] != depth + 1:
                print(f"WARNING: Child depth {child['depth']} doesn't match expected {depth + 1}. Fixing...")
                child['depth'] = depth + 1
            html += render_interactive_node_html(child, current_path)
        html += '</div>'
    else:
        answer_id = f"answer-{node_id}"
        html += f"""
        <div class="answer-node" id="{answer_id}">
            <h3>Answer:</h3>
            <div>{node.get('answer', 'No answer available')}</div>
            <button onclick="showDetails('{answer_id}', false); event.stopPropagation();">View Full Answer</button>
        </div>
        """
    
    html += '</div>'
    return html 