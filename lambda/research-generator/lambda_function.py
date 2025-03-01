import json
import boto3
import os
import uuid
from anthropic import Anthropic

# Maximum allowed values for user-configurable parameters
MAX_ALLOWED_RECURSION_DEPTH = 4
MAX_ALLOWED_SUB_QUESTIONS = 5
# Default values
DEFAULT_RECURSION_DEPTH = 2
DEFAULT_SUB_QUESTIONS = 3
DEFAULT_RECURSION_THRESHOLD = 1

def lambda_handler(event, context):
    # CORS headers to include in all responses
    cors_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'OPTIONS,POST',
        'Access-Control-Allow-Headers': 'Content-Type'
    }
    
    # Handle preflight OPTIONS request
    if event.get('httpMethod') == 'OPTIONS':
        return build_response(200, {})
    
    # Get the parameter name from environment variables
    parameter_name = os.environ['ANTHROPIC_API_KEY_SECRET_NAME']
    
    session = boto3.session.Session()
    ssm_client = session.client('ssm')
    
    try:
        print(f"Attempting to get parameter: {parameter_name}")
        response = ssm_client.get_parameter(
            Name=parameter_name,
            WithDecryption=True
        )
        
        api_key = response['Parameter']['Value']
        
        # Log key details safely for debugging
        key_length = len(api_key) if api_key else 0
        key_prefix = api_key[:4] if key_length >= 4 else api_key
        key_suffix = api_key[-4:] if key_length >= 8 else ""
        print(f"API Key retrieved - Length: {key_length}, Prefix: {key_prefix}, Suffix: {key_suffix}")
        print(f"API Key format check - Starts with 'sk-ant-': {api_key.startswith('sk-ant-') if api_key else False}")
        
        # Initialize Anthropic client
        client = Anthropic(api_key=api_key)
        print("Successfully initialized Anthropic client")

        # Parse the incoming event
        try:
            body = json.loads(event.get('body', '{}'))
            main_question = body.get('expression')
            
            if not main_question:
                return build_response(400, {
                    'error': 'Missing required parameter. Please provide a research topic.'
                })

            # Get user-specified parameters with validation
            max_recursion_depth = min(
                int(body.get('max_recursion_depth', DEFAULT_RECURSION_DEPTH)), 
                MAX_ALLOWED_RECURSION_DEPTH
            )
            max_sub_questions = min(
                int(body.get('max_sub_questions', DEFAULT_SUB_QUESTIONS)), 
                MAX_ALLOWED_SUB_QUESTIONS
            )
            recursion_threshold = min(
                int(body.get('recursion_threshold', DEFAULT_RECURSION_THRESHOLD)), 
                2  # Maximum threshold value is 2
            )
            
            # Ensure values are within valid ranges
            max_recursion_depth = max(0, max_recursion_depth)
            max_sub_questions = max(1, max_sub_questions)
            recursion_threshold = max(0, recursion_threshold)
            
            print(f"Processing main question: {main_question}")
            print(f"Using parameters - max_recursion_depth: {max_recursion_depth}, " +
                  f"max_sub_questions: {max_sub_questions}, recursion_threshold: {recursion_threshold}")
            
            # Start the recursive question breakdown and answering process
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
            
            # Generate the final aggregated answer
            final_answer = aggregate_answers(question_tree, client)
            
            # Generate a visualization of the thought tree
            tree_visualization = generate_tree_visualization(question_tree)
            
            # Include the parameters used in the response
            return build_response(200, {
                'explanation': final_answer,
                'tree_visualization': tree_visualization,
                'question_tree': question_tree,
                'parameters_used': {
                    'max_recursion_depth': max_recursion_depth,
                    'max_sub_questions': max_sub_questions,
                    'recursion_threshold': recursion_threshold
                },
                'success': True,
                'formatted': True
            })
            
        except json.JSONDecodeError:
            return build_response(400, {'error': 'Invalid JSON in request body'})
        except ValueError as ve:
            return build_response(400, {'error': f'Invalid parameter value: {str(ve)}'})
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        return build_response(500, {'error': f'Internal server error: {str(e)}'})

def process_question_node(node, client, max_recursion_depth=DEFAULT_RECURSION_DEPTH, 
                         max_sub_questions=DEFAULT_SUB_QUESTIONS, recursion_threshold=DEFAULT_RECURSION_THRESHOLD):
    """
    Recursively process a question node:
    1. Determine if the question needs to be broken down
    2. If yes, break it down and process each sub-question
    3. If no, get the answer for this question
    """
    depth = node['depth']
    question = node['question']
    
    print(f"Processing question at depth {depth}: {question}")
    
    # Check if we've reached the maximum recursion depth
    if depth >= max_recursion_depth:
        print(f"WARNING: Maximum recursion depth ({max_recursion_depth}) reached for question: {question}")
        
        # Instead of error message, get a concise summary
        node['answer'] = get_concise_summary_for_broad_question(question, client)
        node['needs_breakdown'] = False
        node['max_depth_reached'] = True
        return
    
    # For questions at deeper levels, be more conservative about breaking them down
    if depth > 1:
        # At deeper levels, we should be more conservative about breaking down questions
        print(f"At depth {depth}, being more conservative about breaking down: {question}")
    
    # Determine if the question needs to be broken down
    needs_breakdown, sub_questions = should_break_down_question(question, client, recursion_threshold)
    
    # Additional check: if we're at depth > 0 and have no sub-questions or only one, don't break down
    if needs_breakdown and depth > 0 and (not sub_questions or len(sub_questions) <= 1):
        print(f"Overriding breakdown decision at depth {depth} because only {len(sub_questions)} sub-questions were generated")
        needs_breakdown = False
    
    node['needs_breakdown'] = needs_breakdown
    
    if needs_breakdown:
        print(f"Breaking down question into {len(sub_questions)} sub-questions")
        # Process each sub-question recursively
        for sub_q in sub_questions:
            sub_node = {
                'id': str(uuid.uuid4()),
                'question': sub_q,
                'depth': depth + 1,
                'children': []
            }
            node['children'].append(sub_node)
            process_question_node(sub_node, client, max_recursion_depth, max_sub_questions, recursion_threshold)
    else:
        # This is a leaf node, check if it's too vague
        if is_question_too_vague(question, client):
            print(f"Question is too vague, providing vanilla response: {question}")
            node['answer'] = get_vanilla_response_for_vague_question(question, client)
            node['is_vague'] = True
        else:
            # Get a detailed answer for a specific question
            print(f"Getting answer for leaf question: {question}")
            node['answer'] = get_answer_for_question(question, client)

def should_break_down_question(question, client, recursion_threshold=DEFAULT_RECURSION_THRESHOLD):
    """
    Use Anthropic to determine if a question should be broken down into sub-questions.
    Returns a tuple of (needs_breakdown, sub_questions)
    """
    # Adjust the prompt based on the recursion threshold
    conservative_guidance = ""
    if recursion_threshold >= 1:
        conservative_guidance = """
IMPORTANT: Be conservative about breaking down questions. Only break down a question if ALL of these criteria are met:
1. The question covers multiple distinct topics or aspects that would benefit from separate analysis
2. The question is broad enough that a direct answer would be superficial
3. Breaking it down would lead to more precise and valuable answers
"""
    if recursion_threshold >= 2:
        conservative_guidance += """
EXTREMELY IMPORTANT: Be VERY conservative about breaking down questions. The strong preference is to NOT break down questions unless absolutely necessary.
Only break down questions that are extremely broad and complex, covering multiple distinct domains of knowledge.
"""

    prompt = f"""You are a research assistant tasked with breaking down complex questions into simpler sub-questions.

Given the following question, determine if it should be broken down into sub-questions for more thorough research.
{conservative_guidance}
If the question is already specific, focused on a single aspect, or can be answered comprehensively in one go, do NOT break it down.

Question: {question}

Your response should be in JSON format:
{{
  "needs_breakdown": true/false,
  "reasoning": "Brief explanation of why this question should or should not be broken down",
  "sub_questions": ["sub-question 1", "sub-question 2", ...]
}}

If needs_breakdown is false, sub_questions can be an empty array.
"""

    # Adjust temperature based on recursion threshold - lower temperature for more conservative behavior
    temperature = 0.2
    if recursion_threshold >= 1:
        temperature = 0.1
    
    system_message = "You are a helpful research assistant that breaks down complex questions into simpler sub-questions."
    if recursion_threshold >= 1:
        system_message += " Be conservative about breaking down questions - only do so when truly necessary."
    if recursion_threshold >= 2:
        system_message += " The strong preference is to NOT break down questions unless absolutely necessary."
    system_message += " Always respond in valid JSON format."

    message = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1000,
        temperature=temperature,
        system=system_message,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Extract the JSON response
    content = extract_content(message)
    
    try:
        # Find JSON in the response
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_str = content[json_start:json_end]
            result = json.loads(json_str)
            
            # Log the reasoning for debugging
            if 'reasoning' in result:
                print(f"Breakdown decision reasoning: {result['reasoning']}")
            
            # Apply additional threshold-based filtering
            needs_breakdown = result.get('needs_breakdown', False)
            if needs_breakdown and recursion_threshold >= 2:
                # For very conservative mode, randomly reject some breakdown decisions
                import random
                if random.random() < 0.5:  # 50% chance to override to false
                    print("Very conservative mode: Overriding breakdown decision to false")
                    needs_breakdown = False
            
            # Ensure we don't exceed the maximum number of sub-questions
            if needs_breakdown:
                sub_questions = result.get('sub_questions', [])
                if len(sub_questions) > max_sub_questions:
                    sub_questions = sub_questions[:max_sub_questions]
                return needs_breakdown, sub_questions
            return False, []
        else:
            print(f"Could not find JSON in response: {content}")
            return False, []
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Response content: {content}")
        return False, []

def get_answer_for_question(question, client):
    """
    Use Anthropic to get an answer for a specific question
    """
    prompt = f"""You are a research assistant.
    
    Please provide a detailed answer to the following question: {question}
    
    Your answer should be comprehensive but focused specifically on this question.
    """
    
    message = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1000,
        temperature=0.5,
        system="You are a helpful and friendly research assistant that explains complex concepts in simple terms. Format your response with HTML tags for better readability: use <h3> for section titles, <p> for paragraphs, <ol> and <li> for numbered steps, <strong> for emphasis, and <hr> for section dividers.",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return extract_content(message)

def aggregate_answers(question_tree, client):
    """
    Aggregate the answers from the question tree into a comprehensive final answer
    """
    # First, ensure all branches have been answered
    if not has_complete_answers(question_tree):
        return "Error: Not all questions have been answered. Please try again."
    
    # Create a structured representation of the question tree for Claude
    tree_representation = format_tree_for_aggregation(question_tree)
    
    # Check if any nodes reached max depth or were too vague
    max_depth_reached = has_max_depth_nodes(question_tree)
    has_vague_questions = has_vague_question_nodes(question_tree)
    
    special_notes = ""
    if max_depth_reached:
        special_notes += """
Note: Some questions in this research were very broad and reached our system's maximum depth for breaking down questions.
For these broad questions, I've provided concise overviews rather than comprehensive answers.
You may want to ask more specific follow-up questions about these areas for more detailed information.
"""
    
    if has_vague_questions:
        special_notes += """
Note: Some questions in this research were identified as too vague to provide detailed, specific answers.
For these vague questions, I've provided general guidance and suggestions for making them more specific.
Consider refining these questions with more context or parameters for more detailed information.
"""
    
    prompt = f"""You are a research assistant tasked with synthesizing information from multiple sources.

I've broken down a complex question into sub-questions and found answers to each. Now I need you to synthesize this information into a comprehensive answer to the original question.

Original question: {question_tree['question']}

{special_notes}

Here is the breakdown of questions and answers:

{tree_representation}

Please synthesize all this information into a comprehensive, well-structured answer to the original question. Use HTML formatting for better readability.
"""

    message = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=2000,
        temperature=0.5,
        system="You are a helpful research assistant that synthesizes information from multiple sources. Format your response with HTML tags for better readability: use <h3> for section titles, <p> for paragraphs, <ol> and <li> for numbered steps, <strong> for emphasis, and <hr> for section dividers.",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    content = extract_content(message)
    
    # Add disclaimers at the beginning if needed
    disclaimers = ""
    if max_depth_reached:
        disclaimers += """<div class="note" style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin-bottom: 20px;">
        <strong>Note:</strong> Some questions in this research were very broad and reached our system's maximum depth for breaking down questions.
        For these broad areas, concise overviews are provided rather than comprehensive answers.
        Consider asking more specific follow-up questions about these areas for more detailed information.
        </div>"""
    
    if has_vague_questions:
        disclaimers += """<div class="note" style="background-color: #e6f7ff; border-left: 4px solid #1890ff; padding: 15px; margin-bottom: 20px;">
        <strong>Note:</strong> Some questions in this research were identified as too vague to provide detailed, specific answers.
        For these questions, general guidance and suggestions for making them more specific are provided.
        Consider refining these questions with more context or parameters for more detailed information.
        </div>"""
    
    if disclaimers:
        return disclaimers + content
    
    return content

def has_complete_answers(node):
    """
    Check if all leaf nodes in the tree have answers
    """
    if node['needs_breakdown']:
        # This is not a leaf node, check all children
        return all(has_complete_answers(child) for child in node['children'])
    else:
        # This is a leaf node, check if it has an answer
        return 'answer' in node and node['answer']

def format_tree_for_aggregation(node, indent=0):
    """
    Format the question tree for aggregation, with proper indentation
    """
    result = "  " * indent + f"Question: {node['question']}\n"
    
    if node['needs_breakdown']:
        result += "  " * indent + "Sub-questions and answers:\n"
        for child in node['children']:
            result += format_tree_for_aggregation(child, indent + 1)
    else:
        result += "  " * indent + f"Answer: {node['answer']}\n\n"
    
    return result

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
            
            // Initialize: expand the root node
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

def render_interactive_node_html(node):
    """
    Render a single node of the question tree as interactive HTML
    """
    depth = node['depth']
    node_id = node['id']
    
    # Add a special class if this node reached max depth or is vague
    max_depth_class = " max-depth-node" if node.get('max_depth_reached', False) else ""
    vague_class = " vague-node" if node.get('is_vague', False) else ""
    
    html = f"""
    <div class="node question-node{max_depth_class}{vague_class}" id="{node_id}">
        <div class="node-header" onclick="toggleNode('{node_id}')">
            <span class="depth-indicator">Depth {depth}:</span>
            <span class="node-title">Question: {node['question']}</span>
            <span class="toggle-icon">+</span>
        </div>
        <div class="node-content">
            <button onclick="showDetails('{node_id}', true); event.stopPropagation();">View Details</button>
            {f'<span class="max-depth-badge">Max Depth</span>' if node.get('max_depth_reached', False) else ''}
            {f'<span class="vague-badge">Vague Question</span>' if node.get('is_vague', False) else ''}
        </div>
    """
    
    if node.get('needs_breakdown', False):
        html += '<div class="children">'
        for child in node['children']:
            html += render_interactive_node_html(child)
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

def extract_content(message):
    """
    Extract text content from an Anthropic API response
    """
    if hasattr(message, 'content'):
        content = message.content
        if isinstance(content, list):
            # If content is a list of blocks
            text_parts = []
            for item in content:
                if hasattr(item, 'text'):
                    text_parts.append(item.text)
                elif hasattr(item, 'value'):
                    text_parts.append(item.value)
                elif isinstance(item, str):
                    text_parts.append(item)
            return " ".join(text_parts)
        elif isinstance(content, str):
            # If content is already a string
            return content
        else:
            # Fallback: convert to string representation
            return str(content)
    else:
        return str(message)

def build_response(status_code, body):
    """Helper function to build CORS-compliant responses."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST',
            'Access-Control-Allow-Headers': 'Content-Type'
        },
        'body': json.dumps(body)
    }

def get_concise_summary_for_broad_question(question, client):
    """
    Get a concise summary for a question that has reached maximum recursion depth
    """
    prompt = f"""You are a research assistant.
    
    The following question is very broad and has reached the maximum recursion depth in our system:
    
    {question}
    
    Please provide a CONCISE summary (no more than 300 words) that:
    1. Acknowledges that the question is broad and could be broken down further
    2. Provides a high-level overview of the key points related to this question
    3. Suggests how the user might narrow their focus for more detailed information
    
    Format your response with HTML tags for better readability.
    """
    
    message = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=800,
        temperature=0.5,
        system="You are a helpful research assistant that provides concise summaries of broad topics. Format your response with HTML tags for better readability: use <h3> for section titles, <p> for paragraphs, <div class='note'> for special notes, <strong> for emphasis.",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    content = extract_content(message)
    
    # Add a disclaimer at the beginning
    disclaimer = """<div class="note" style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin-bottom: 20px;">
    <strong>Note:</strong> This question is very broad and has reached our system's maximum depth for breaking down questions. 
    The following is a concise overview rather than a comprehensive answer. Consider asking more specific questions for detailed information.
    </div>"""
    
    return disclaimer + content

def has_max_depth_nodes(node):
    """
    Check if the tree has any nodes that reached maximum depth
    """
    if node.get('max_depth_reached', False):
        return True
    
    if node.get('needs_breakdown', False):
        # Check children
        for child in node['children']:
            if has_max_depth_nodes(child):
                return True
    
    return False

def is_question_too_vague(question, client):
    """
    Determine if a question is too vague to provide a detailed answer.
    Returns True if the question is too vague, False otherwise.
    """
    prompt = f"""You are a research assistant tasked with evaluating questions.

Given the following question, determine if it is too vague to provide a detailed, specific answer:

Question: {question}

A question is too vague if:
1. It lacks specific context or parameters
2. It could be interpreted in many different ways
3. It's overly broad without clear focus
4. It uses ambiguous terms without clarification

Your response should be in JSON format:
{{
  "is_vague": true/false,
  "reasoning": "Brief explanation of why this question is or is not too vague"
}}
"""

    message = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=500,
        temperature=0.2,
        system="You are a helpful research assistant that evaluates the specificity of questions. Always respond in valid JSON format.",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Extract the JSON response
    content = extract_content(message)
    
    try:
        # Find JSON in the response
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_str = content[json_start:json_end]
            result = json.loads(json_str)
            
            # Log the reasoning for debugging
            if 'reasoning' in result:
                print(f"Vagueness evaluation reasoning: {result['reasoning']}")
            
            return result.get('is_vague', False)
        else:
            print(f"Could not find JSON in response: {content}")
            return False
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Response content: {content}")
        return False

def get_vanilla_response_for_vague_question(question, client):
    """
    Provide a vanilla response for questions that are too vague.
    """
    prompt = f"""You are a research assistant.
    
    The following question is too vague to provide a detailed, specific answer:
    
    {question}
    
    Please provide a vanilla response that:
    1. Acknowledges that the question is vague or lacks specificity
    2. Explains why more specific details would be helpful
    3. Suggests ways to make the question more specific
    4. Provides some general information about the topic, but without going into great detail
    
    Format your response with HTML tags for better readability.
    """
    
    message = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=800,
        temperature=0.5,
        system="You are a helpful research assistant that provides guidance on vague questions. Format your response with HTML tags for better readability: use <h3> for section titles, <p> for paragraphs, <div class='note'> for special notes, <strong> for emphasis.",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    content = extract_content(message)
    
    # Add a disclaimer at the beginning
    disclaimer = """<div class="note" style="background-color: #e6f7ff; border-left: 4px solid #1890ff; padding: 15px; margin-bottom: 20px;">
    <strong>Note:</strong> This question is quite vague or general. For more detailed information, consider asking a more specific question.
    </div>"""
    
    return disclaimer + content

def has_vague_question_nodes(node):
    """
    Check if the tree has any nodes that were identified as too vague
    """
    if node.get('is_vague', False):
        return True
    
    if node.get('needs_breakdown', False):
        # Check children
        for child in node['children']:
            if has_vague_question_nodes(child):
                return True
    
    return False