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

# Model configuration
DEFAULT_MODEL = "claude-3-haiku-20240307"  # Fastest Claude model
DEFAULT_SYNTHESIS_MAX_TOKENS = 1500  # Reduced from 2000
DEFAULT_ANSWER_MAX_TOKENS = 800  # Reduced from 1000
DEFAULT_EVALUATION_MAX_TOKENS = 600  # Reduced from 1000

# Token reduction factors based on depth
def get_token_limit_for_depth(base_limit, depth):
    """
    Calculate token limit based on depth - deeper nodes get fewer tokens
    """
    if depth == 0:
        return base_limit
    elif depth == 1:
        return int(base_limit * 0.75)  # 75% of base limit
    elif depth == 2:
        return int(base_limit * 0.5)   # 50% of base limit
    else:
        return int(base_limit * 0.25)   # 25% of base limit for depth 3+

def lambda_handler(event, context):
    # Check if this is a Lambda Function URL invocation (it will have 'requestContext.http' in the event)
    is_function_url = 'requestContext' in event and 'http' in event.get('requestContext', {})
    
    # CORS headers to include in all responses (only when not using Function URL)
    cors_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'OPTIONS,POST',
        'Access-Control-Allow-Headers': 'Content-Type'
    }
    
    # Handle preflight OPTIONS request
    if event.get('httpMethod') == 'OPTIONS':
        return build_response(200, {}, not is_function_url)
    
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
                }, not is_function_url)

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
            }, not is_function_url)
            
        except json.JSONDecodeError:
            return build_response(400, {'error': 'Invalid JSON in request body'}, not is_function_url)
        except ValueError as ve:
            return build_response(400, {'error': f'Invalid parameter value: {str(ve)}'}, not is_function_url)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        return build_response(500, {'error': f'Internal server error: {str(e)}'}, not is_function_url)

def process_question_node(node, client, max_recursion_depth=DEFAULT_RECURSION_DEPTH, 
                         max_sub_questions=DEFAULT_SUB_QUESTIONS, recursion_threshold=DEFAULT_RECURSION_THRESHOLD,
                         original_question=None):
    """
    Recursively process a question node:
    1. Determine if the question needs to be broken down
    2. If yes, break it down and process each sub-question
    3. If no, get the answer for this question
    """
    depth = node['depth']
    question = node['question']
    
    # Track the original question for context
    if original_question is None:
        original_question = question  # The root question is the original question
    
    print(f"Processing question at depth {depth}: {question}")
    
    # Check if we've reached the maximum recursion depth
    if depth >= max_recursion_depth:
        print(f"WARNING: Maximum recursion depth ({max_recursion_depth}) reached for question: {question}")
        
        # Instead of error message, get a concise summary
        node['answer'] = get_concise_summary_for_broad_question(question, client, depth)
        node['needs_breakdown'] = False
        node['max_depth_reached'] = True
        return
    
    # For questions at deeper levels, be more conservative about breaking them down
    if depth > 1:
        # At deeper levels, we should be more conservative about breaking down questions
        print(f"At depth {depth}, being more conservative about breaking down: {question}")
    
    # Determine if the question needs to be broken down
    needs_breakdown, sub_questions = should_break_down_question(question, client, recursion_threshold, max_sub_questions, depth)
    
    # Additional check: if we're at depth > 0 and have no sub-questions or only one, don't break down
    if needs_breakdown and depth > 0 and (not sub_questions or len(sub_questions) <= 1):
        print(f"Overriding breakdown decision at depth {depth} because only {len(sub_questions)} sub-questions were generated")
        needs_breakdown = False
    
    # Validate that sub-questions are actually simpler than the parent question and stay on topic
    if needs_breakdown and depth > 0 and sub_questions:
        validated_sub_questions = validate_sub_questions_simplicity(question, sub_questions, client, depth)
        if not validated_sub_questions:
            print(f"Overriding breakdown decision at depth {depth} because sub-questions were not valid (not simpler or off-topic)")
            needs_breakdown = False
        else:
            sub_questions = validated_sub_questions
    
    # Additional check: ensure sub-questions are relevant to the original question
    if needs_breakdown and depth > 0 and sub_questions:
        relevant_sub_questions = validate_sub_questions_relevance(original_question, sub_questions, client)
        if not relevant_sub_questions:
            print(f"Overriding breakdown decision at depth {depth} because sub-questions were not relevant to the original question")
            needs_breakdown = False
        else:
            sub_questions = relevant_sub_questions
    
    node['needs_breakdown'] = needs_breakdown
    
    if needs_breakdown:
        print(f"Breaking down question into {len(sub_questions)} sub-questions")
        # Process each sub-question recursively
        node['children'] = []  # Ensure children is initialized as an empty list
        for sub_q in sub_questions:
            sub_node = {
                'id': str(uuid.uuid4()),
                'question': sub_q,
                'depth': depth + 1,  # Explicitly set depth as parent depth + 1
                'children': [],
                'parent_question': question,  # Store the parent question for context
                'original_question': original_question  # Store the original question for context
            }
            node['children'].append(sub_node)
            process_question_node(sub_node, client, max_recursion_depth, max_sub_questions, recursion_threshold, original_question)
    else:
        # This is a leaf node, check if it's too vague
        if is_question_too_vague(question, client):
            print(f"Question is too vague, providing vanilla response: {question}")
            node['answer'] = get_vanilla_response_for_vague_question(question, client, depth)
            node['is_vague'] = True
        else:
            # Get a detailed answer for a specific question
            print(f"Getting answer for leaf question: {question}")
            # Pass parent context if available
            parent_question = node.get('parent_question', None)
            # Also pass the original question for broader context
            node['answer'] = get_answer_for_question(question, client, parent_question, depth, original_question)

def validate_sub_questions_simplicity(parent_question, sub_questions, client, depth):
    """
    Validate that sub-questions are actually simpler than the parent question.
    Returns a filtered list of sub-questions that are simpler, or an empty list if none are simpler.
    """
    if depth == 0 or not sub_questions:
        return sub_questions  # At depth 0, no simplification check needed
    
    prompt = f"""You are a research assistant tasked with evaluating whether sub-questions are simpler than their parent question and stay on topic.

Parent question: {parent_question}

Sub-questions:
{json.dumps(sub_questions, indent=2)}

For each sub-question, determine if it meets BOTH of these criteria:
1. It is GENUINELY SIMPLER than the parent question (more specific, narrower scope, less complex)
2. It STAYS ON TOPIC and is directly relevant to the parent question (not tangential or introducing unrelated topics)

A good sub-question:
- Is more specific and narrower in scope
- Focuses on a single, well-defined aspect of the parent question
- Is answerable with less complexity
- Does not introduce new complexity or broaden the scope
- Remains directly relevant to the parent question
- Does not deviate into tangential topics

Your response should be in JSON format:
{{
  "evaluations": [
    {{
      "sub_question": "sub-question 1",
      "is_valid": true/false,
      "reasoning": "Brief explanation focusing on simplicity and topic relevance"
    }},
    ...
  ]
}}
"""

    message = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=DEFAULT_EVALUATION_MAX_TOKENS,
        temperature=0.1,  # Low temperature for consistent evaluation
        system="You are a helpful research assistant that evaluates the quality of sub-questions. Always respond in valid JSON format. Be strict about ensuring sub-questions are both simpler AND stay on topic.",
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
            
            # Filter sub-questions to only include those that are simpler and on topic
            valid_sub_questions = []
            for eval_item in result.get('evaluations', []):
                if eval_item.get('is_valid', False):
                    valid_sub_questions.append(eval_item.get('sub_question'))
                else:
                    print(f"Removing invalid sub-question: {eval_item.get('sub_question')}")
                    print(f"Reasoning: {eval_item.get('reasoning')}")
            
            return valid_sub_questions
        else:
            print(f"Could not find JSON in response: {content}")
            return []
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Response content: {content}")
        return []

def should_break_down_question(question, client, recursion_threshold=DEFAULT_RECURSION_THRESHOLD, max_sub_questions=DEFAULT_SUB_QUESTIONS, depth=0):
    """
    Use Anthropic to determine if a question should be broken down into sub-questions.
    Returns a tuple of (needs_breakdown, sub_questions)
    """
    # Adjust the prompt based on the recursion threshold and depth
    conservative_guidance = ""
    simplification_guidance = ""
    topic_focus_guidance = ""
    
    # Add depth-based guidance to ensure questions get simpler
    if depth > 0:
        simplification_guidance = f"""
CRITICAL: You are at recursion depth {depth}. At this depth, it is ESSENTIAL that any sub-questions you generate are SIGNIFICANTLY SIMPLER than the parent question.
Each sub-question MUST:
1. Be more specific and narrower in scope than the parent question
2. Focus on a single, well-defined aspect of the parent question
3. Be answerable with less complexity than the parent question
4. Avoid introducing new complexity or broadening the scope

DO NOT create sub-questions that:
- Are as complex as the original question
- Introduce new topics not directly related to the parent question
- Require their own complex breakdown
- Are vague or general in nature
"""

    # Add topic focus guidance to ensure sub-questions stay on topic
    topic_focus_guidance = """
EXTREMELY IMPORTANT: All sub-questions MUST be directly related to the original question and should not deviate from the main topic.
Each sub-question should:
1. Explore a specific aspect of the ORIGINAL question
2. Maintain clear relevance to the main topic
3. Not introduce tangential or only loosely related topics
4. Together with other sub-questions, comprehensively cover the original question.

The goal is to break down the question into more manageable parts while ensuring all parts remain focused on answering the original question.
"""

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
{simplification_guidance}
{topic_focus_guidance}
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

    # Adjust temperature based on recursion threshold and depth - lower temperature for more conservative behavior
    temperature = 0.2
    if recursion_threshold >= 1 or depth > 0:
        temperature = 0.1
    
    system_message = "You are a helpful research assistant that breaks down complex questions into simpler sub-questions."
    if recursion_threshold >= 1:
        system_message += " Be conservative about breaking down questions - only do so when truly necessary."
    if recursion_threshold >= 2:
        system_message += " The strong preference is to NOT break down questions unless absolutely necessary."
    if depth > 0:
        system_message += f" At depth {depth}, you MUST ensure that sub-questions are SIGNIFICANTLY SIMPLER than their parent question."
    system_message += " Always respond in valid JSON format."
    system_message += " Ensure all sub-questions remain directly focused on the original topic and don't introduce tangential subjects."

    message = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=DEFAULT_EVALUATION_MAX_TOKENS,
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

def get_answer_for_question(question, client, parent_question=None, depth=0, original_question=None):
    """
    Use Anthropic to get an answer for a specific question
    """
    context_prompt = ""
    if parent_question:
        context_prompt = f"""
This question is part of a larger research question: "{parent_question}"
Your answer should be relevant to this broader context while focusing specifically on the sub-question.
"""
    
    # Add original question context if available and different from parent
    if original_question and original_question != parent_question:
        context_prompt += f"""
This is part of research on the original question: "{original_question}"
Ensure your answer contributes to understanding this original research question.
"""
    
    # Adjust token limit based on depth
    token_limit = get_token_limit_for_depth(DEFAULT_ANSWER_MAX_TOKENS, depth)
    
    # Adjust the prompt based on depth to encourage brevity at deeper levels
    brevity_guidance = ""
    if depth >= 1:
        brevity_guidance = "Be concise and focus only on the most important points."
    if depth >= 2:
        brevity_guidance = "Be very brief and focus only on the essential information."
    if depth >= 3:
        brevity_guidance = "Provide only the most critical information in a highly condensed format."
    
    prompt = f"""You are a research assistant.
    
    Please provide a detailed answer to the following question: {question}
    
    {context_prompt}
    
    Your answer should be comprehensive but focused specifically on this question.
    Be concise and direct in your response while covering the key points.
    {brevity_guidance}
    """
    
    message = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=token_limit,
        temperature=0.5,
        system="You are a helpful and friendly research assistant that explains complex concepts in simple terms. Format your response with HTML tags for better readability: use <h3> for section titles, <p> for paragraphs, <ol> and <li> for numbered steps, <strong> for emphasis, and <hr> for section dividers. Be concise and direct.",
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
Be concise and direct while ensuring all key points are covered.
"""

    message = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=DEFAULT_SYNTHESIS_MAX_TOKENS,
        temperature=0.5,
        system="You are a helpful research assistant that synthesizes information from multiple sources. Format your response with HTML tags for better readability: use <h3> for section titles, <p> for paragraphs, <ol> and <li> for numbered steps, <strong> for emphasis, and <hr> for section dividers. Be concise and direct in your explanations.",
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

def build_response(status_code, body, include_cors=True):
    """Helper function to build responses, optionally with CORS headers."""
    response = {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
        },
        'body': json.dumps(body)
    }
    
    # Add CORS headers only if needed (not for Function URL invocations)
    if include_cors:
        response['headers'].update({
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST',
            'Access-Control-Allow-Headers': 'Content-Type'
        })
    
    return response

def get_concise_summary_for_broad_question(question, client, depth=0):
    """
    Get a concise summary for a question that has reached maximum recursion depth
    """
    # Adjust token limit based on depth
    token_limit = get_token_limit_for_depth(DEFAULT_ANSWER_MAX_TOKENS, depth)
    
    prompt = f"""You are a research assistant.
    
    The following question is very broad and has reached the maximum recursion depth in our system:
    
    {question}
    
    Please provide a CONCISE summary (no more than {300 - depth * 50} words) that:
    1. Acknowledges that the question is broad and could be broken down further
    2. Provides a high-level overview of the key points related to this question
    3. Suggests how the user might narrow their focus for more detailed information
    
    Format your response with HTML tags for better readability.
    """
    
    message = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=token_limit,
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

def get_vanilla_response_for_vague_question(question, client, depth=0):
    """
    Provide a vanilla response for questions that are too vague.
    """
    # Adjust token limit based on depth
    token_limit = get_token_limit_for_depth(DEFAULT_ANSWER_MAX_TOKENS, depth)
    
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
        model=DEFAULT_MODEL,
        max_tokens=token_limit,
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

def validate_sub_questions_relevance(original_question, sub_questions, client):
    """
    Validate that sub-questions are relevant to the original question.
    Returns a filtered list of sub-questions that are relevant, or an empty list if none are relevant.
    """
    if not sub_questions:
        return []
    
    prompt = f"""You are a research assistant tasked with evaluating whether sub-questions are relevant to the original research question.

Original research question: {original_question}

Sub-questions:
{json.dumps(sub_questions, indent=2)}

For each sub-question, determine if it is DIRECTLY RELEVANT to the original research question. A relevant sub-question:
1. Addresses a specific aspect of the original question
2. Helps answer the original question when combined with other sub-questions
3. Does not introduce topics that are tangential or unrelated to the original question
4. Maintains the same general subject matter as the original question

Your response should be in JSON format:
{{
  "evaluations": [
    {{
      "sub_question": "sub-question 1",
      "is_relevant": true/false,
      "reasoning": "Brief explanation of why this sub-question is or is not relevant to the original question"
    }},
    ...
  ]
}}
"""

    message = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=DEFAULT_EVALUATION_MAX_TOKENS,
        temperature=0.1,  # Low temperature for consistent evaluation
        system="You are a helpful research assistant that evaluates the relevance of sub-questions to the original research question. Always respond in valid JSON format. Be strict about ensuring sub-questions are directly relevant to the original question.",
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
            
            # Filter sub-questions to only include those that are relevant
            relevant_sub_questions = []
            for eval_item in result.get('evaluations', []):
                if eval_item.get('is_relevant', False):
                    relevant_sub_questions.append(eval_item.get('sub_question'))
                else:
                    print(f"Removing irrelevant sub-question: {eval_item.get('sub_question')}")
                    print(f"Reasoning: {eval_item.get('reasoning')}")
            
            return relevant_sub_questions
        else:
            print(f"Could not find JSON in response: {content}")
            return []
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Response content: {content}")
        return []